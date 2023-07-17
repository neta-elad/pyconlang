from dataclasses import dataclass, field
from functools import reduce
from typing import cast

from ..domain import (
    Affix,
    Component,
    Compound,
    Fusion,
    Joiner,
    Lang,
    Lexeme,
    Morpheme,
    PartOfSpeech,
    Prefix,
    Rule,
    Suffix,
    Tags,
    Word,
)
from ..errors import AffixDefinitionMissingForm, AffixDefinitionMissingVar


@dataclass(eq=True, frozen=True)
class TemplateName:
    name: str


@dataclass(eq=True, frozen=True)
class Var:
    prefixes: tuple[Prefix, ...] = field(default_factory=tuple)
    """prefixes are stored in reversed order"""

    suffixes: tuple[Suffix, ...] = field(default_factory=tuple)

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: list[Prefix], suffixes: list[Suffix]
    ) -> "Var":
        return cls(tuple(reversed(prefixes)), tuple(suffixes))

    def show(self, stem: str) -> str:
        for affix in self.prefixes + self.suffixes:
            stem = affix.combine(stem, affix.name)

        return stem

    def __str__(self) -> str:
        return self.show("$")


@dataclass(eq=True, frozen=True)
class Template:
    name: TemplateName
    tags: Tags
    vars: tuple[Var, ...]

    @classmethod
    def from_args(cls, name: TemplateName, tags: Tags, *var_args: Var) -> "Template":
        return cls(name, tags, var_args)


@dataclass(eq=True, frozen=True)
class Entry:
    template: TemplateName | None
    lexeme: Lexeme
    tags: Tags
    form: Word[Fusion]
    part_of_speech: PartOfSpeech
    definition: str

    def description(self) -> str:
        return f"{self.part_of_speech} {self.definition}"


@dataclass(eq=True, frozen=True)
class AffixDefinition:
    stressed: bool
    affix: Affix
    tags: Tags = field(default_factory=Tags)
    era: Rule | None = field(default=None)
    form: Word[Fusion] | Var | None = field(default=None)
    sources: tuple[Lexeme, ...] = field(
        default_factory=tuple
    )  # or Form - can bare Proto appear?
    description: str = field(default="")

    def get_era(self) -> Rule | None:
        if self.era is not None:
            return self.era
        elif (
            isinstance(self.form, Component)
            and isinstance(self.form.form, Fusion)
            and isinstance(self.form.form.stem, Morpheme)
        ):
            return self.form.form.stem.era
        else:
            return None

    def is_var(self) -> bool:
        return self.form is not None and isinstance(self.form, Var)

    def get_form(self) -> Word[Fusion]:
        if self.form is not None and not isinstance(self.form, Var):
            return self.form
        elif self.sources:
            return reduce(
                lambda head, tail: Compound(head, Joiner.head(), tail),
                map(
                    lambda source: cast(Word[Fusion], Component(Fusion(source))),
                    self.sources,
                ),
            )
        else:
            raise AffixDefinitionMissingForm(self)

    def get_var(self) -> Var:
        if self.form is not None and isinstance(self.form, Var):
            return self.form
        else:
            raise AffixDefinitionMissingVar(self)

    def to_entry(self) -> Entry:
        return Entry(
            None,
            self.affix.to_lexeme(),
            self.tags,
            self.get_form(),
            PartOfSpeech("afx"),
            self.description,
        )


@dataclass(eq=True, frozen=True)
class LangParent:
    lang: Lang
    parent: Lang
