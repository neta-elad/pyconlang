from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple, Union

from ..checksum import checksum
from ..types import (
    Affix,
    AffixDefinition,
    Compound,
    Describable,
    Entry,
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

LEXICON_PATH = Path("lexicon.txt")


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

    def resolve_affix(self, affix: Affix) -> ResolvedAffix:
        definition = self.get_affix(affix)
        return ResolvedAffix(
            definition.stressed,
            definition.affix.type,
            definition.get_era(),
            self.resolve(definition.get_form()),
        )

    def resolve(self, form: Unit) -> ResolvedForm:
        compound = Compound.from_form(form)

        affixes = tuple(self.resolve_affix(affix) for affix in compound.affixes)

        match stem := compound.stem:
            case Morpheme():
                return ResolvedForm(stem, affixes)
            case Lexeme():
                return self.resolve(self.get_entry(stem).form).extend(*affixes)
            case Compound():
                return self.resolve(stem).extend(*affixes)

    def resolve_with_affixes(
        self, form: Unit, affixes: Tuple[Affix, ...]
    ) -> ResolvedForm:
        resolved_affixes = tuple(self.resolve_affix(affix) for affix in affixes)
        resolved = self.resolve(form)
        return ResolvedForm(resolved.stem, resolved.affixes + resolved_affixes)

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

    def lookup(self, record: Describable) -> List[Tuple[Describable, str]]:
        match record:
            case Affix():
                return self.singleton_lookup(record, self.get_affix(record).description)
            case Lexeme():
                entry = self.get_entry(record)
                return self.singleton_lookup(
                    record, f"{entry.part_of_speech} {entry.definition}"
                )
            case Morpheme():
                return self.singleton_lookup(record, str(record))
            case Compound():
                return self.lookup_records(record.stem, *record.affixes)

    def lookup_records(self, *records: Describable) -> List[Tuple[Describable, str]]:
        return list(chain(*map(self.lookup, records)))

    @staticmethod
    def singleton_lookup(
        record: Describable, description: str
    ) -> List[Tuple[Describable, str]]:
        return [(record, description)]
