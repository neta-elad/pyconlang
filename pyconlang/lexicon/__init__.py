from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple, Union

from ..checksum import checksum
from ..types import (
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
from .errors import MissingAffix, MissingLexeme, MissingTemplate, UnexpectedRecord
from .parser import lexicon

LEXICON_PATH = Path("lexicon.pycl")


@dataclass
class Lexicon:
    entries: Set[Entry]
    affixes: Set[AffixDefinition]
    templates: Set[Template]

    @staticmethod
    def checksum() -> bytes:
        return checksum(LEXICON_PATH)

    @classmethod
    def from_path(cls, path: Path = LEXICON_PATH) -> "Lexicon":
        return cls.from_string(path.read_text())

    @classmethod
    def from_string(cls, string: str) -> "Lexicon":
        return cls.from_iterable(lexicon.parse_string(string + "\n", parse_all=True))

    @classmethod
    def from_iterable(
        cls, iterable: Iterable[Union[Entry, AffixDefinition, Template]]
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

    def resolve_affix(self, affix: Affix) -> List[ResolvedAffix]:
        definition = self.get_affix(affix)
        if definition.is_var():
            return list(
                chain(
                    *[
                        self.resolve_affix(sub_affix)
                        for sub_affix in definition.get_var().affixes
                    ]
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
        affixes = tuple(chain(*[self.resolve_affix(affix) for affix in fusion.affixes]))
        return self.resolve(fusion.stem).extend(*affixes)

    def resolve_compound(self, compound: Compound) -> ResolvedForm:
        head = self.resolve(compound.head)
        tail = self.resolve(compound.tail)
        tail_as_affix = ResolvedAffix.from_compound(compound, tail)
        return head.extend(tail_as_affix)

    def resolve_with_affixes(
        self, form: Unit, affixes: Tuple[Affix, ...]
    ) -> ResolvedForm:
        resolved_affixes = tuple(
            chain(*[self.resolve_affix(affix) for affix in affixes])
        )
        resolved = self.resolve(form)
        return resolved.extend(*resolved_affixes)

    def substitute(self, var: Var, form: Unit) -> ResolvedForm:
        return self.resolve_with_affixes(form, var.affixes)

    def get_vars(self, name: Optional[TemplateName]) -> Tuple[Var, ...]:
        if name is None:
            return (Var(()),)
        else:
            for template in self.templates:
                if template.name == name:
                    return template.vars

            raise MissingTemplate(name.name)

    def resolve_entry(self, entry: Entry) -> List[ResolvedForm]:
        return [
            self.substitute(var, entry.form) for var in self.get_vars(entry.template)
        ]

    def define(self, record: Definable) -> str:
        match record:
            case Affix():
                return self.get_affix(record).description

            case Lexeme():
                return self.get_entry(record).description()

    def lookup(self, record: Describable) -> List[Tuple[Describable, str]]:
        match record:
            case Affix():
                return self.singleton_lookup(record, self.get_affix(record).description)
            case Lexeme():
                entry = self.get_entry(record)
                return self.singleton_lookup(record, entry.description())
            case Morpheme():
                return self.singleton_lookup(record, str(record))
            case Fusion():
                return self.lookup_records(record.stem, *record.affixes)
            case Compound():
                return self.lookup(record.head) + self.lookup(record.tail)

    def lookup_records(self, *records: Describable) -> List[Tuple[Describable, str]]:
        return list(chain(*map(self.lookup, records)))

    @staticmethod
    def singleton_lookup(
        record: Describable, description: str
    ) -> List[Tuple[Describable, str]]:
        return [(record, description)]
