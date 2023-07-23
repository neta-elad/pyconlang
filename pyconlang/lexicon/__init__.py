from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path

from .. import CHANGES_PATH, LEXICON_PATH
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
    Prefix,
    Record,
    ResolvedForm,
    Scope,
    Scoped,
    Suffix,
)
from ..parser import continue_lines
from .domain import AffixDefinition, Entry, ScopeDefinition, Template, TemplateName, Var
from .errors import MissingAffix, MissingLexeme, MissingTemplate, UnexpectedRecord
from .parser import parse_lexicon


@dataclass
class Lexicon:
    entries: set[Entry]
    affixes: set[AffixDefinition]
    templates: set[Template]
    scopes: set[ScopeDefinition]

    @classmethod
    def from_path(cls, path: Path = LEXICON_PATH) -> "Lexicon":
        return cls.from_string(path.read_text(), path.parent)

    @classmethod
    def from_string(cls, string: str, parent: Path = Path()) -> "Lexicon":
        return cls.from_lines(string.splitlines(), parent)

    @classmethod
    def from_lines(cls, lines: Iterable[str], parent: Path) -> "Lexicon":
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
                path = cls.resolve_if_relative(line, parent)
                return cls.resolve_paths(
                    parse_lexicon(continue_lines(path.read_text().splitlines())),
                    path.parent,
                )

            case _:
                return [line]

    @classmethod
    def from_iterable(
        cls, iterable: Iterable[Entry | AffixDefinition | Template | ScopeDefinition]
    ) -> "Lexicon":
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
    def entry_mapping(self) -> dict[tuple[Scope, LexemeFusion], Entry]:
        return {(entry.tags.scope, entry.lexeme): entry for entry in self.entries} | {
            (definition.tags.scope, definition.affix.to_fusion()): definition.to_entry()
            for definition in self.affixes
            if not definition.is_var()
        }

    def get_entry(self, lexeme: Lexeme, scope: Scope = Scope()) -> Entry:
        fusion = Fusion(lexeme)
        if (scope, fusion) in self.entry_mapping:
            return self.entry_mapping[(scope, fusion)]

        parent = self.parent(scope)
        if scope == parent:
            raise MissingLexeme(f"{lexeme.name} in {scope}")
        else:
            return self.get_entry(lexeme, parent)

    @cached_property
    def affix_mapping(self) -> dict[tuple[Scope, Affix], AffixDefinition]:
        return {
            (definition.tags.scope, definition.affix): definition
            for definition in self.affixes
        }

    def get_affix(self, affix: Affix, scope: Scope = Scope()) -> AffixDefinition:
        if (scope, affix) in self.affix_mapping:
            return self.affix_mapping[(scope, affix)]

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
                return self.resolve(self.get_entry(form, scope).form, scope)
            case _:
                return self.resolve(form, scope)

    def resolve_fusion(
        self, fusion: DefaultFusion, scope: Scope = Scope()
    ) -> ResolvedForm:
        prefixes = fusion.prefixes
        suffixes = fusion.suffixes
        max_total_length = len(prefixes) + len(suffixes)
        for k in range(max_total_length, -1, -1):
            for i in range(0, 1 + len(prefixes)):
                j = 1 + k - i
                if 0 <= j <= 1 + len(suffixes):
                    this_prefixes = prefixes[i:]
                    rest_prefixes = prefixes[:i]
                    this_suffixes = suffixes[:j]
                    rest_suffixes = suffixes[j:]
                    if isinstance(fusion.stem, Scoped):
                        override_scope = fusion.stem.scope or scope
                        this_fusion = Fusion(
                            fusion.stem.scoped, this_prefixes, this_suffixes
                        )
                        if (override_scope, this_fusion) in self.entry_mapping:
                            return self.extend_with_affixes(
                                self.resolve(
                                    self.entry_mapping[
                                        (override_scope, this_fusion)
                                    ].form,
                                    scope,
                                ),
                                scope,
                                *(rest_prefixes + rest_suffixes),
                            )

        return self.extend_with_affixes(
            self.resolve_any(fusion.stem, scope),
            scope,
            *(fusion.prefixes + fusion.suffixes),
        )

    def resolve_compound(
        self, compound: Compound[DefaultFusion], scope: Scope = Scope()
    ) -> ResolvedForm:
        head = self.resolve(compound.head, scope)
        tail = self.resolve(compound.tail, scope)
        return Compound(
            head,
            compound.joiner,
            tail,
        )

    def extend_with_affixes(
        self, form: ResolvedForm, scope: Scope, *affixes: Affix
    ) -> ResolvedForm:
        for affix in affixes:
            form = self.extend_with_affix(form, affix, scope)

        return form

    def extend_with_affix(
        self, form: ResolvedForm, affix: Affix, scope: Scope = Scope()
    ) -> ResolvedForm:
        definition = self.get_affix(affix, scope)
        if definition.is_var():
            return self.extend_with_affixes(
                form,
                scope,
                *(definition.get_var().prefixes + definition.get_var().suffixes),
            )
        else:
            match definition.affix:
                case Prefix():
                    if definition.stressed:
                        return Compound(
                            self.resolve(definition.get_form(), scope),
                            Joiner.head(definition.get_era()),
                            form,
                        )
                    else:
                        return Compound(
                            self.resolve(definition.get_form(), scope),
                            Joiner.tail(definition.get_era()),
                            form,
                        )
                case Suffix():
                    if definition.stressed:
                        return Compound(
                            form,
                            Joiner.tail(definition.get_era()),
                            self.resolve(definition.get_form(), scope),
                        )
                    else:
                        return Compound(
                            form,
                            Joiner.head(definition.get_era()),
                            self.resolve(definition.get_form(), scope),
                        )

    def substitute(  # todo: remove?
        self, var: Var, form: DefaultWord, scope: Scope = Scope()
    ) -> ResolvedForm:
        return self.extend_with_affixes(
            self.resolve(form, scope), scope, *(var.prefixes + var.suffixes)
        )

    def get_vars(self, name: TemplateName | None) -> tuple[Var, ...]:
        if name is None:
            return (Var((), ()),)
        else:
            for template in self.templates:
                if template.name == name:
                    return template.vars

            raise MissingTemplate(name.name)

    def form(self, record: Definable, scope: Scope = Scope()) -> DefaultWord:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record, scope).get_form()

            case Lexeme():
                return self.get_entry(record, scope).form

    def define(self, record: Definable, scope: Scope = Scope()) -> str:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record, scope).description

            case Lexeme():
                return self.get_entry(record, scope).description()

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

    def parent(self, scope: Scope) -> Scope:
        return self.parents.get(scope, Scope())

    def changes_for(self, scope: Scope) -> Path:
        return self.changes.get(scope, CHANGES_PATH)
