from dataclasses import dataclass
from typing import Iterable, Optional, Set, Tuple, Union

from ..types import (
    Affix,
    AffixDefinition,
    Canonical,
    Entry,
    Form,
    Proto,
    ResolvedAffix,
    ResolvedForm,
    Template,
    TemplateName,
    Var,
)


@dataclass
class Lexicon:
    entries: Set[Entry]
    affixes: Set[AffixDefinition]
    templates: Set[Template]

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

    def get_resolved_affix(self, affix_name: str) -> ResolvedAffix:
        definition = self.get_affix(affix_name)
        return ResolvedAffix(
            definition.stressed,
            definition.affix,
            definition.get_era(),
            self.resolve(definition.get_form()),
        )

    def resolve(self, form: Form) -> ResolvedForm:
        match form:
            case Proto():
                return ResolvedForm(form, ())
            case _:
                affixes = tuple(
                    self.get_resolved_affix(affix.name) for affix in form.affixes
                )
                resolved = self.resolve(self.get_entry(form.stem).form)
                return ResolvedForm(resolved.stem, resolved.affixes + affixes)

    def resolve_with_affixes(
        self, form: Form, affixes: Tuple[Affix, ...]
    ) -> ResolvedForm:
        resolved_affixes = tuple(
            self.get_resolved_affix(affix.name) for affix in affixes
        )
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
