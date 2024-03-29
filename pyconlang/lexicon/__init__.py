from collections.abc import Iterable
from dataclasses import dataclass, replace
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Self

from .. import CHANGES_PATH, LEXICON_PATH
from ..config import config, config_scope_as
from ..domain import (
    Affix,
    Component,
    Compound,
    DefaultFusion,
    DefaultWord,
    Definable,
    Describable,
    Fusion,
    Joiner,
    Lexeme,
    LexemeFusion,
    Morpheme,
    NonScopedDefinable,
    Prefix,
    Record,
    ResolvedForm,
    Rule,
    Scope,
    Scoped,
    ScopedAffix,
    Suffix,
)
from ..parser import continue_lines
from .domain import (
    AffixDefinition,
    Entry,
    ScopeDefinition,
    Template,
    TemplateName,
    VarFusion,
)
from .errors import MissingAffix, MissingLexeme, MissingTemplate, UnexpectedRecord
from .parser import parse_lexicon


@dataclass
class Lexicon:
    entries: set[Entry]
    affixes: set[AffixDefinition]
    templates: set[Template]
    scopes: set[ScopeDefinition]

    @classmethod
    def from_path(cls, path: Path = LEXICON_PATH) -> Self:
        return cls.from_iterable(cls.resolve_path(path, Path()))

    @classmethod
    def from_string(cls, string: str, parent: Path = Path()) -> Self:
        return cls.from_lines(string.splitlines(), parent)

    @classmethod
    def from_lines(cls, lines: Iterable[str], parent: Path) -> Self:
        return cls.from_iterable(
            cls.resolve_paths(parse_lexicon(continue_lines(lines)), parent)
        )

    @classmethod
    def resolve_paths(
        cls,
        lines: Iterable[Entry | AffixDefinition | Template | ScopeDefinition | Path],
        parent: Path,
    ) -> Iterable[Entry | AffixDefinition | ScopeDefinition | Template]:
        return (
            definition
            for line in lines
            for definition in cls.resolve_line(line, parent)
        )

    @classmethod
    def resolve_if_relative(cls, path: Path, parent: Path) -> Path:
        if path.is_absolute():
            return path

        return parent / path

    @classmethod
    def resolve_line(
        cls,
        line: Entry | AffixDefinition | Template | ScopeDefinition | Path,
        parent: Path,
    ) -> Iterable[Entry | AffixDefinition | Template | ScopeDefinition]:
        match line:
            case Path():
                return cls.resolve_path(line, parent)

            case _:
                return [line]

    @classmethod
    def resolve_path(
        cls, path: Path, parent: Path
    ) -> Iterable[Entry | AffixDefinition | Template | ScopeDefinition]:
        path = cls.resolve_if_relative(path, parent)
        file_scope = config().scope
        if path.stem.startswith("%"):
            file_scope = path.stem[1:]
        with config_scope_as(file_scope):
            return list(
                cls.resolve_paths(
                    parse_lexicon(continue_lines(path.read_text().splitlines())),
                    path.parent,
                )
            )

    @classmethod
    def from_iterable(
        cls, iterable: Iterable[Entry | AffixDefinition | Template | ScopeDefinition]
    ) -> Self:
        entries = set()
        affixes = set()
        templates = set()
        scopes = set()
        for record in iterable:
            match record:
                case Entry():
                    entries.add(record)
                case AffixDefinition():
                    affixes.add(record)
                case Template():
                    templates.add(record)
                case ScopeDefinition():
                    scopes.add(record)
                case _:
                    raise UnexpectedRecord(record)

        return cls(entries, affixes, templates, scopes)

    @cached_property
    def entry_mapping(self) -> dict[Scope, dict[LexemeFusion, Entry]]:
        mapping = dict[Scope, dict[LexemeFusion, Entry]]()
        for entry in self.entries:
            scope = entry.tags.scope
            mapping.setdefault(scope, {})
            mapping[scope][entry.lexeme] = entry

        for affix in self.affixes:
            if affix.is_var():
                continue
            scope = affix.tags.scope
            mapping.setdefault(scope, {})
            mapping[scope][affix.affix.to_fusion()] = affix.to_entry()

        return mapping

    def get_entry(self, lexeme: Lexeme, scope: Scope = Scope()) -> Entry:
        fusion = Fusion(lexeme)
        if scope in self.entry_mapping and fusion in self.entry_mapping[scope]:
            return self.entry_mapping[scope][fusion]

        parent = self.parent(scope)
        if scope == parent:
            raise MissingLexeme(f"{lexeme.name} in {scope}")
        else:
            return self.get_entry(lexeme, parent)

    @cached_property
    def affix_mapping(self) -> dict[Scope, dict[Affix, AffixDefinition]]:
        mapping = dict[Scope, dict[Affix, AffixDefinition]]()
        for affix in self.affixes:
            scope = affix.tags.scope
            mapping.setdefault(scope, {})
            mapping[scope][affix.affix] = affix

        return mapping

    def get_affix(self, affix: Affix, scope: Scope = Scope()) -> AffixDefinition:
        if scope in self.affix_mapping and affix in self.affix_mapping[scope]:
            return self.affix_mapping[scope][affix]

        parent = self.parent(scope)
        if scope == parent:
            raise MissingAffix(f"{affix.name} in {scope}")
        else:
            return self.get_affix(affix, parent)

    def resolve(self, word: DefaultWord, scope: Scope = Scope()) -> ResolvedForm:
        match word:
            case Component():
                return self.resolve_fusion(word.form, scope)
            case Compound():
                return self.resolve_compound(word, scope)

    def resolve_any(
        self,
        form: DefaultWord | Morpheme | Lexeme | Scoped[Lexeme],
        scope: Scope = Scope(),
    ) -> ResolvedForm:
        match form:
            case Fusion():
                return self.resolve_fusion(form, scope)
            case Morpheme():
                return Component(form)
            case Scoped():
                return self.resolve_any(form.scoped, form.scope or scope)
            case Lexeme():
                entry_form = self.get_entry(form, scope).form
                return self.resolve(entry_form.scoped, entry_form.scope or scope)
            case _:
                return self.resolve(form, scope)

    def to_lexeme_fusion(self, fusion: DefaultFusion) -> LexemeFusion | None:
        if not isinstance(fusion.stem, Scoped):
            return None

        if fusion.stem.scope is not None:
            return None

        lexeme = fusion.stem.scoped

        prefixes: list[Prefix] = []

        for prefix in fusion.prefixes:
            if prefix.scope is not None:
                return None

            prefixes.append(prefix.scoped)

        suffixes: list[Suffix] = []

        for suffix in fusion.suffixes:
            if suffix.scope is not None:
                return None

            suffixes.append(suffix.scoped)

        return Fusion(lexeme, tuple(prefixes), tuple(suffixes))

    def resolve_fusion(
        self, fusion: DefaultFusion, scope: Scope = Scope()
    ) -> ResolvedForm:
        prefixes = len(fusion.prefixes)
        suffixes = len(fusion.suffixes)
        max_total_length = prefixes + suffixes
        for k in range(max_total_length, -1, -1):
            for i in range(max(0, k - suffixes), 1 + min(k, prefixes)):
                j = k - i
                this_fusion = fusion[:i, :j]
                this_lexeme_fusion = self.to_lexeme_fusion(this_fusion)
                if (
                    this_lexeme_fusion is not None
                    and scope in self.entry_mapping
                    and this_lexeme_fusion in self.entry_mapping[scope]
                ):
                    entry = self.entry_mapping[scope][this_lexeme_fusion]
                    entry_form = entry.form
                    return self.extend_with_affixes(
                        self.resolve(
                            entry_form.scoped,
                            entry_form.scope or entry.tags.scope or scope,
                        ),
                        scope,
                        *fusion[i:, j:].affixes(),
                    )

        return self.extend_with_affixes(
            self.resolve_any(fusion.stem, scope),
            scope,
            *fusion.affixes(),
        )

    def resolve_compound(
        self, compound: Compound[DefaultFusion], scope: Scope = Scope()
    ) -> ResolvedForm:
        head = self.resolve(compound.head, scope)
        tail = self.resolve(compound.tail, scope)
        joiner = compound.joiner
        if joiner.era is None and scope in self.default_eras:
            joiner = replace(joiner, era=self.default_eras[scope])

        return Compound(
            head,
            joiner,
            tail,
        )

    def extend_with_affixes(
        self, form: ResolvedForm, scope: Scope, *affixes: ScopedAffix
    ) -> ResolvedForm:
        for affix in affixes:
            form = self.extend_with_affix(form, affix.scoped, affix.scope or scope)

        return form

    def extend_with_affix(
        self, form: ResolvedForm, affix: Affix, scope: Scope = Scope()
    ) -> ResolvedForm:
        definition = self.get_affix(affix, scope)
        if definition.is_var():
            return self.extend_with_affixes(
                form,
                scope,
                *definition.get_var().affixes(),
            )
        else:
            definition_form = definition.get_form()
            resolved_form = self.resolve(
                definition_form.scoped, definition_form.scope or scope
            )
            match definition.affix:
                case Prefix():
                    if definition.stressed:
                        return Compound(
                            resolved_form,
                            Joiner.head(definition.get_era()),
                            form,
                        )
                    else:
                        return Compound(
                            resolved_form,
                            Joiner.tail(definition.get_era()),
                            form,
                        )
                case Suffix():
                    if definition.stressed:
                        return Compound(
                            form,
                            Joiner.tail(definition.get_era()),
                            resolved_form,
                        )
                    else:
                        return Compound(
                            form,
                            Joiner.head(definition.get_era()),
                            resolved_form,
                        )

    def get_vars(self, name: TemplateName | None) -> tuple[VarFusion, ...]:
        if name is None:
            return (VarFusion("$", (), ()),)
        else:
            for template in self.templates:
                if template.name == name:
                    return template.vars

            raise MissingTemplate(name.name)

    def form(self, record: Definable, scope: Scope = Scope()) -> Scoped[DefaultWord]:
        match record.scoped:
            case Prefix() | Suffix():
                return self.get_affix(record.scoped, record.scope or scope).get_form()

            case Lexeme():
                return self.get_entry(record.scoped, record.scope or scope).form

    def describe(self, record: NonScopedDefinable, scope: Scope = Scope()) -> str:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record, scope).description

            case Lexeme():
                return self.get_entry(record, scope).description()

    def define(self, record: Definable, scope: Scope = Scope()) -> str:
        actual_scope = record.scope or scope
        scope_description = ""
        if actual_scope.name != config().scope:
            scope_description = f" [{actual_scope.name or '<ROOT>'}]"
        return f"{self.describe(record.scoped, actual_scope)}{scope_description}"

    def lookup(
        self, record: Record, scope: Scope = Scope()
    ) -> list[tuple[Describable, str]]:
        match record:
            case Prefix() | Suffix():
                return self.singleton_lookup(
                    record, self.get_affix(record, scope).description
                )
            case Scoped():
                return self.lookup(record.scoped, record.scope or scope)
            case Lexeme():
                entry = self.get_entry(record, scope)
                return self.singleton_lookup(record, entry.description())
            case Morpheme():
                return self.singleton_lookup(record, str(record))
            case Fusion():
                return self.lookup_records(
                    scope, record.stem, *record.prefixes, *record.suffixes
                )
            case Compound():
                return self.lookup(record.head, scope) + self.lookup(record.tail, scope)
            case Component():
                return self.lookup(record.form, scope)

    def lookup_records(
        self, scope: Scope, *records: Record
    ) -> list[tuple[Describable, str]]:
        return list(chain(*map(lambda record: self.lookup(record, scope), records)))

    @staticmethod
    def singleton_lookup(
        record: Describable, description: str
    ) -> list[tuple[Describable, str]]:
        return [(record, description)]

    @cached_property
    def parents(self) -> dict[Scope, Scope]:
        return {definition.scope: definition.parent for definition in self.scopes}

    @cached_property
    def changes(self) -> dict[Scope, Path]:
        return {definition.scope: definition.changes for definition in self.scopes}

    @cached_property
    def default_eras(self) -> dict[Scope, Rule]:
        return {
            definition.scope: definition.default_era
            for definition in self.scopes
            if definition.default_era is not None
        }

    def parent(self, scope: Scope) -> Scope:
        return self.parents.get(scope, Scope())

    def changes_for(self, scope: Scope) -> Path:
        return self.changes.get(scope, CHANGES_PATH)
