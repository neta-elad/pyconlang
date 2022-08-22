from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple, Union

from ..types import (
    Affix,
    AffixDefinition,
    Canonical,
    Compound,
    Entry,
    Form,
    Proto,
    ResolvedAffix,
    ResolvedForm,
    Template,
    TemplateName,
    Var,
)
from .parser import lexicon

LEXICON_PATH = Path("lexicon.txt")


@dataclass
class Lexicon:
    entries: Set[Entry]
    affixes: Set[AffixDefinition]
    templates: Set[Template]

    @staticmethod
    def checksum() -> int:
        return hash(LEXICON_PATH.read_text())

    @classmethod
    def from_path(cls, path: Path = LEXICON_PATH) -> "Lexicon":
        return cls.from_string(path.read_text())

    @classmethod
    def from_string(cls, string: str) -> "Lexicon":
        return cls.from_iterable(lexicon.parse_string(string, parse_all=True))

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
                    raise RuntimeError(f"Unexpected record {record}")

        return cls(entries, affixes, templates)

    def get_entry(self, canonical: Canonical) -> Entry:
        for entry in self.entries:
            if entry.canonical == canonical:
                return entry

        raise KeyError(canonical)

    def get_affix(self, affix_name: str) -> AffixDefinition:
        for affix in self.affixes:
            if affix.affix.name == affix_name:
                return affix

        raise KeyError(affix_name)

    def resolve_affix(self, affix_name: str) -> ResolvedAffix:
        definition = self.get_affix(affix_name)
        return ResolvedAffix(
            definition.stressed,
            definition.affix.type,
            definition.get_era(),
            self.resolve(definition.get_form()),
        )

    def resolve(self, form: Form) -> ResolvedForm:
        compound = Compound.from_form(form)

        affixes = tuple(self.resolve_affix(affix.name) for affix in compound.affixes)

        match stem := compound.stem:
            case Proto():
                return ResolvedForm(stem, affixes)
            case Canonical():
                return self.resolve(self.get_entry(stem).form).extend(*affixes)

    def resolve_with_affixes(
        self, form: Form, affixes: Tuple[Affix, ...]
    ) -> ResolvedForm:
        resolved_affixes = tuple(self.resolve_affix(affix.name) for affix in affixes)
        resolved = self.resolve(form)
        return ResolvedForm(resolved.stem, resolved.affixes + resolved_affixes)

    def substitute(self, var: Var, form: Form) -> ResolvedForm:
        return self.resolve_with_affixes(form, var.affixes)

    def get_vars(self, name: Optional[TemplateName]) -> Tuple[Var, ...]:
        if name is None:
            return (Var(()),)
        else:
            for template in self.templates:
                if template.name == name:
                    return template.vars

            raise KeyError(name)

    def resolve_entry(self, entry: Entry) -> List[ResolvedForm]:
        return [
            self.substitute(var, entry.form) for var in self.get_vars(entry.template)
        ]
