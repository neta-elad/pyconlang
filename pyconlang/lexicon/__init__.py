from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path

from pyconlang import LEXICON_PATH

from ..domain import (
    Affix,
    AffixDefinition,
    Component,
    Compound,
    Definable,
    Describable,
    Entry,
    Fusion,
    Joiner,
    Lexeme,
    Morpheme,
    Prefix,
    Record,
    ResolvedForm,
    Suffix,
    Template,
    TemplateName,
    Var,
    Word,
)
from ..parser import continue_lines
from .errors import MissingAffix, MissingLexeme, MissingTemplate, UnexpectedRecord
from .parser import parse_lexicon


@dataclass
class Lexicon:
    entries: set[Entry]
    affixes: set[AffixDefinition]
    templates: set[Template]

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
        cls, lines: Iterable[Entry | AffixDefinition | Template | Path], parent: Path
    ) -> Iterable[Entry | AffixDefinition | Template]:
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
        cls, line: Entry | AffixDefinition | Template | Path, parent: Path
    ) -> Iterable[Entry | AffixDefinition | Template]:
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
        cls, iterable: Iterable[Entry | AffixDefinition | Template]
    ) -> "Lexicon":
        entries = set()
        affixes = set()
        templates = set()
        for record in iterable:
            match record:
                case Entry():
                    entries.add(record)
                case AffixDefinition():
                    affixes.add(record)
                case Template():
                    templates.add(record)
                case _:
                    raise UnexpectedRecord(record)

        return cls(entries, affixes, templates)

    @cached_property
    def entry_mapping(self) -> dict[Lexeme, Entry]:
        return {entry.lexeme: entry for entry in self.entries} | {
            definition.affix.to_lexeme(): definition.to_entry()
            for definition in self.affixes
            if not definition.is_var()
        }

    def get_entry(self, lexeme: Lexeme) -> Entry:
        if lexeme in self.entry_mapping:
            return self.entry_mapping[lexeme]

        raise MissingLexeme(lexeme.name)

    @cached_property
    def affix_mapping(self) -> dict[Affix, AffixDefinition]:
        return {definition.affix: definition for definition in self.affixes}

    def get_affix(self, affix: Affix) -> AffixDefinition:
        if affix in self.affix_mapping:
            return self.affix_mapping[affix]

        raise MissingAffix(affix.name)

    def resolve(self, word: Word[Fusion]) -> ResolvedForm:
        match word:
            case Component():
                return self.resolve_fusion(word.form)
            case Compound():
                return self.resolve_compound(word)

    def resolve_any(
        self, form: Word[Fusion] | Fusion | Morpheme | Lexeme
    ) -> ResolvedForm:
        match form:
            case Fusion():
                return self.resolve_fusion(form)
            case Morpheme():
                return Component(form)
            case Lexeme():
                return self.resolve(self.get_entry(form).form)
            case _:
                return self.resolve(form)

    def resolve_fusion(self, fusion: Fusion) -> ResolvedForm:
        # prefixes = self.resolve_affixes(fusion.prefixes)  # todo: remove?
        # suffixes = self.resolve_affixes(fusion.suffixes)
        return self.extend_with_affixes(
            self.resolve_any(fusion.stem), *(fusion.prefixes + fusion.suffixes)
        )

    def resolve_compound(self, compound: Compound[Fusion]) -> ResolvedForm:
        head = self.resolve(compound.head)
        tail = self.resolve(compound.tail)
        return Compound(
            head,
            compound.joiner,
            tail,
        )

    def extend_with_affixes(self, form: ResolvedForm, *affixes: Affix) -> ResolvedForm:
        for affix in affixes:
            form = self.extend_with_affix(form, affix)

        return form

    def extend_with_affix(self, form: ResolvedForm, affix: Affix) -> ResolvedForm:
        definition = self.get_affix(affix)
        if definition.is_var():
            return self.extend_with_affixes(
                form, *(definition.get_var().prefixes + definition.get_var().suffixes)
            )
        else:
            match definition.affix:
                case Prefix():
                    if definition.stressed:
                        return Compound(
                            self.resolve(definition.get_form()),
                            Joiner.head(definition.get_era()),
                            form,
                        )
                    else:
                        return Compound(
                            self.resolve(definition.get_form()),
                            Joiner.tail(definition.get_era()),
                            form,
                        )
                case Suffix():
                    if definition.stressed:
                        return Compound(
                            form,
                            Joiner.tail(definition.get_era()),
                            self.resolve(definition.get_form()),
                        )
                    else:
                        return Compound(
                            form,
                            Joiner.head(definition.get_era()),
                            self.resolve(definition.get_form()),
                        )

    def substitute(self, var: Var, form: Word[Fusion]) -> ResolvedForm:
        return self.extend_with_affixes(
            self.resolve(form), *(var.prefixes + var.suffixes)
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
            self.substitute(var, entry.form) for var in self.get_vars(entry.template)
        ]

    def form(self, record: Definable) -> Word[Fusion]:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record).get_form()

            case Lexeme():
                return self.get_entry(record).form

    def resolve_definable(self, record: Definable) -> ResolvedForm:
        return self.resolve(self.form(record))

    def define(self, record: Definable) -> str:
        match record:
            case Prefix() | Suffix():
                return self.get_affix(record).description

            case Lexeme():
                return self.get_entry(record).description()

    def lookup(self, record: Record) -> list[tuple[Describable, str]]:
        match record:
            case Prefix() | Suffix():
                return self.singleton_lookup(record, self.get_affix(record).description)
            case Lexeme():
                entry = self.get_entry(record)
                return self.singleton_lookup(record, entry.description())
            case Morpheme():
                return self.singleton_lookup(record, str(record))
            case Fusion():
                return self.lookup_records(
                    record.stem, *record.prefixes, *record.suffixes
                )
            case Compound():
                return self.lookup(record.head) + self.lookup(record.tail)
            case Component():
                return self.lookup(record.form)

    def lookup_records(self, *records: Record) -> list[tuple[Describable, str]]:
        return list(chain(*map(self.lookup, records)))

    @staticmethod
    def singleton_lookup(
        record: Describable, description: str
    ) -> list[tuple[Describable, str]]:
        return [(record, description)]
