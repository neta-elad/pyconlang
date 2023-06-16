from collections.abc import Iterable
from dataclasses import dataclass
from itertools import chain
from pathlib import Path

from ..checksum import checksum
from ..domain import (
    Affix,
    AffixDefinition,
    Compound,
    Definable,
    Describable,
    Entry,
    Fusion,
    Lexeme,
    Morpheme,
    ResolvedAffix,
    ResolvedForm,
    Template,
    TemplateName,
    Unit,
    Var,
)
from ..parser import continue_lines
from .errors import MissingAffix, MissingLexeme, MissingTemplate, UnexpectedRecord
from .parser import parse_lexicon

LEXICON_PATH = Path("lexicon.pycl")


@dataclass
class Lexicon:
    entries: set[Entry]
    affixes: set[AffixDefinition]
    templates: set[Template]

    @staticmethod
    def checksum() -> bytes:
        return checksum(LEXICON_PATH)

    @classmethod
    def from_path(cls, path: Path = LEXICON_PATH) -> "Lexicon":
        return cls.from_string(path.read_text())

    @classmethod
    def from_string(cls, string: str) -> "Lexicon":
        return cls.from_lines(string.splitlines())

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> "Lexicon":
        return cls.from_iterable(parse_lexicon(continue_lines(lines)))

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

    def get_entry(self, lexeme: Lexeme) -> Entry:
        for entry in self.entries:
            if entry.lexeme == lexeme:
                return entry

        raise MissingLexeme(lexeme.name)

    def get_affix(self, affix: Affix) -> AffixDefinition:
        for possible_affix in self.affixes:
            if possible_affix.affix.name == affix.name:
                return possible_affix

        raise MissingAffix(affix.name)

    def resolve_affix(self, affix: Affix) -> list[ResolvedAffix]:
        definition = self.get_affix(affix)
        if definition.is_var():
            return list(
                chain(
                    *[
                        self.resolve_affix(sub_affix)
                        for sub_affix in definition.get_var().prefixes
                    ],
                    *[
                        self.resolve_affix(sub_affix)
                        for sub_affix in definition.get_var().suffixes
                    ],
                )
            )
        else:
            return [
                ResolvedAffix(
                    definition.stressed,
                    definition.affix.type,
                    definition.get_era(),
                    self.resolve(definition.get_form()),
                )
            ]

    def resolve_affixes(self, affixes: tuple[Affix, ...]) -> tuple[ResolvedAffix, ...]:
        return tuple(chain(*[self.resolve_affix(affix) for affix in affixes]))

    def resolve(self, unit: Unit) -> ResolvedForm:
        match unit:
            case Morpheme():
                return ResolvedForm(unit)
            case Lexeme():
                return self.resolve(self.get_entry(unit).form)
            case Fusion():
                return self.resolve_fusion(unit)
            case Compound():
                return self.resolve_compound(unit)

    def resolve_fusion(self, fusion: Fusion) -> ResolvedForm:
        prefixes = self.resolve_affixes(fusion.prefixes)
        suffixes = self.resolve_affixes(fusion.suffixes)
        return self.resolve(fusion.stem).extend(prefixes, suffixes)

    def resolve_compound(self, compound: Compound) -> ResolvedForm:
        head = self.resolve(compound.head)
        tail = self.resolve(compound.tail)
        tail_as_affix = ResolvedAffix.from_compound(compound, tail)
        return head.extend_any(tail_as_affix)

    def resolve_with_affixes(
        self, form: Unit, prefixes: tuple[Affix, ...], suffixes: tuple[Affix, ...]
    ) -> ResolvedForm:
        resolved_prefixes = self.resolve_affixes(prefixes)
        resolved_suffixes = self.resolve_affixes(suffixes)
        resolved = self.resolve(form)
        return resolved.extend(resolved_prefixes, resolved_suffixes)

    def substitute(self, var: Var, form: Unit) -> ResolvedForm:
        return self.resolve_with_affixes(form, var.prefixes, var.suffixes)

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

    def form(self, record: Definable) -> Unit:
        match record:
            case Affix():
                return self.get_affix(record).get_form()

            case Lexeme():
                return self.get_entry(record).form

    def resolve_definable(self, record: Definable) -> ResolvedForm:
        return self.resolve(self.form(record))

    def define(self, record: Definable) -> str:
        match record:
            case Affix():
                return self.get_affix(record).description

            case Lexeme():
                return self.get_entry(record).description()

    def lookup(self, record: Describable) -> list[tuple[Describable, str]]:
        match record:
            case Affix():
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

    def lookup_records(self, *records: Describable) -> list[tuple[Describable, str]]:
        return list(chain(*map(self.lookup, records)))

    @staticmethod
    def singleton_lookup(
        record: Describable, description: str
    ) -> list[tuple[Describable, str]]:
        return [(record, description)]
