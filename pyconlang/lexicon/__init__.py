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
    Lang,
    LangLexeme,
    Lexeme,
    LexemeFusion,
    Morpheme,
    Prefix,
    Record,
    ResolvedForm,
    Suffix,
)
from ..parser import continue_lines
from .domain import AffixDefinition, Entry, LangDefinition, Template, TemplateName, Var
from .errors import MissingAffix, MissingLexeme, MissingTemplate, UnexpectedRecord
from .parser import parse_lexicon


@dataclass
class Lexicon:
    entries: set[Entry]
    affixes: set[AffixDefinition]
    templates: set[Template]
    langs: set[LangDefinition]

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
        lines: Iterable[Entry | AffixDefinition | Template | LangDefinition | Path],
        parent: Path,
    ) -> Iterable[Entry | AffixDefinition | LangDefinition | Template]:
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
        line: Entry | AffixDefinition | Template | LangDefinition | Path,
        parent: Path,
    ) -> Iterable[Entry | AffixDefinition | Template | LangDefinition]:
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
        cls, iterable: Iterable[Entry | AffixDefinition | Template | LangDefinition]
    ) -> "Lexicon":
        entries = set()
        affixes = set()
        templates = set()
        lang_parents = set()
        for record in iterable:
            match record:
                case Entry():
                    entries.add(record)
                case AffixDefinition():
                    affixes.add(record)
                case Template():
                    templates.add(record)
                case LangDefinition():
                    lang_parents.add(record)
                case _:
                    raise UnexpectedRecord(record)

        return cls(entries, affixes, templates, lang_parents)

    @cached_property
    def entry_mapping(self) -> dict[tuple[Lang, LexemeFusion], Entry]:
        return {(entry.tags.lang, entry.lexeme): entry for entry in self.entries} | {
            (definition.tags.lang, definition.affix.to_fusion()): definition.to_entry()
            for definition in self.affixes
            if not definition.is_var()
        }

    def get_entry(self, lexeme: Lexeme, lang: Lang = Lang()) -> Entry:
        fusion = Fusion(lexeme)
        if (lang, fusion) in self.entry_mapping:
            return self.entry_mapping[(lang, fusion)]

        parent = self.parent(lang)
        if lang == parent:
            raise MissingLexeme(f"{lexeme.name} in {lang}")
        else:
            return self.get_entry(lexeme, parent)

    @cached_property
    def affix_mapping(self) -> dict[tuple[Lang, Affix], AffixDefinition]:
        return {
            (definition.tags.lang, definition.affix): definition
            for definition in self.affixes
        }

    def get_affix(self, affix: Affix, lang: Lang = Lang()) -> AffixDefinition:
        if (lang, affix) in self.affix_mapping:
            return self.affix_mapping[(lang, affix)]

        parent = self.parent(lang)
        if lang == parent:
            raise MissingAffix(f"{affix.name} in {lang}")
        else:
            return self.get_affix(affix, parent)

    def resolve(self, word: DefaultWord, lang: Lang = Lang()) -> ResolvedForm:
        match word:
            case Component():
                return self.resolve_fusion(word.form, lang)
            case Compound():
                return self.resolve_compound(word, lang)

    def resolve_any(
        self, form: DefaultWord | Morpheme | Lexeme | LangLexeme, lang: Lang = Lang()
    ) -> ResolvedForm:
        match form:
            case Fusion():
                return self.resolve_fusion(form, lang)
            case Morpheme():
                return Component(form)
            case LangLexeme():
                return self.resolve_any(form.lexeme, form.lang or lang)
            case Lexeme():
                return self.resolve(self.get_entry(form, lang).form, lang)
            case _:
                return self.resolve(form, lang)

    def resolve_fusion(
        self, fusion: DefaultFusion, lang: Lang = Lang()
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
                    if isinstance(fusion.stem, LangLexeme):
                        override_lang = fusion.stem.lang or lang
                        this_fusion = Fusion(
                            fusion.stem.lexeme, this_prefixes, this_suffixes
                        )
                        if (override_lang, this_fusion) in self.entry_mapping:
                            return self.extend_with_affixes(
                                self.resolve(
                                    self.entry_mapping[
                                        (override_lang, this_fusion)
                                    ].form,
                                    lang,
                                ),
                                lang,
                                *(rest_prefixes + rest_suffixes),
                            )

        return self.extend_with_affixes(
            self.resolve_any(fusion.stem, lang),
            lang,
            *(fusion.prefixes + fusion.suffixes),
        )

    def resolve_compound(
        self, compound: Compound[DefaultFusion], lang: Lang = Lang()
    ) -> ResolvedForm:
        head = self.resolve(compound.head, lang)
        tail = self.resolve(compound.tail, lang)
        return Compound(
            head,
            compound.joiner,
            tail,
        )

    def extend_with_affixes(
        self, form: ResolvedForm, lang: Lang, *affixes: Affix
    ) -> ResolvedForm:
        for affix in affixes:
            form = self.extend_with_affix(form, affix, lang)

        return form

    def extend_with_affix(
        self, form: ResolvedForm, affix: Affix, lang: Lang = Lang()
    ) -> ResolvedForm:
        definition = self.get_affix(affix, lang)
        if definition.is_var():
            return self.extend_with_affixes(
                form,
                lang,
                *(definition.get_var().prefixes + definition.get_var().suffixes),
            )
        else:
            match definition.affix:
                case Prefix():
                    if definition.stressed:
                        return Compound(
                            self.resolve(definition.get_form(), lang),
                            Joiner.head(definition.get_era()),
                            form,
                        )
                    else:
                        return Compound(
                            self.resolve(definition.get_form(), lang),
                            Joiner.tail(definition.get_era()),
                            form,
                        )
                case Suffix():
                    if definition.stressed:
                        return Compound(
                            form,
                            Joiner.tail(definition.get_era()),
                            self.resolve(definition.get_form(), lang),
                        )
                    else:
                        return Compound(
                            form,
                            Joiner.head(definition.get_era()),
                            self.resolve(definition.get_form(), lang),
                        )

    def substitute(
        self, var: Var, form: DefaultWord, lang: Lang = Lang()
    ) -> ResolvedForm:
        return self.extend_with_affixes(
            self.resolve(form, lang), lang, *(var.prefixes + var.suffixes)
        )

    def get_vars(self, name: TemplateName | None) -> tuple[Var, ...]:
        if name is None:
            return (Var((), ()),)
        else:
            for template in self.templates:
                if template.name == name:
                    return template.vars

            raise MissingTemplate(name.name)

    def resolve_entry(self, entry: Entry) -> list[ResolvedForm]:
        return [
            self.substitute(var, entry.form, entry.tags.lang)
            for var in self.get_vars(entry.template)
        ]

    def form(self, record: Definable, lang: Lang = Lang()) -> DefaultWord:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record, lang).get_form()

            case Lexeme():
                return self.get_entry(record, lang).form

    def resolve_definable(self, record: Definable, lang: Lang = Lang()) -> ResolvedForm:
        return self.resolve(self.form(record, lang), lang)

    def define(self, record: Definable, lang: Lang = Lang()) -> str:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record, lang).description

            case Lexeme():
                return self.get_entry(record, lang).description()

    def lookup(
        self, record: Record, lang: Lang = Lang()
    ) -> list[tuple[Describable, str]]:
        match record:
            case Prefix() | Suffix():
                return self.singleton_lookup(
                    record, self.get_affix(record, lang).description
                )
            case LangLexeme():
                return self.lookup(record.lexeme, record.lang or lang)
            case Lexeme():
                entry = self.get_entry(record, lang)
                return self.singleton_lookup(record, entry.description())
            case Morpheme():
                return self.singleton_lookup(record, str(record))
            case Fusion():
                return self.lookup_records(
                    lang, record.stem, *record.prefixes, *record.suffixes
                )
            case Compound():
                return self.lookup(record.head, lang) + self.lookup(record.tail, lang)
            case Component():
                return self.lookup(record.form, lang)

    def lookup_records(
        self, lang: Lang, *records: Record
    ) -> list[tuple[Describable, str]]:
        return list(chain(*map(lambda record: self.lookup(record, lang), records)))

    @staticmethod
    def singleton_lookup(
        record: Describable, description: str
    ) -> list[tuple[Describable, str]]:
        return [(record, description)]

    @cached_property
    def parents(self) -> dict[Lang, Lang]:
        return {lang_def.lang: lang_def.parent for lang_def in self.langs}

    @cached_property
    def changes(self) -> dict[Lang, Path]:
        return {lang_def.lang: lang_def.changes for lang_def in self.langs}

    def parent(self, lang: Lang) -> Lang:
        return self.parents.get(lang, Lang())

    def changes_for(self, lang: Lang) -> Path:
        return self.changes.get(lang, CHANGES_PATH)
