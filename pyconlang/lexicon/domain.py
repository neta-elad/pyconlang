from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path
from typing import Literal, cast

from .. import CHANGES_PATH
from ..domain import (
    Affix,
    Component,
    Compound,
    DefaultWord,
    Fusion,
    Joiner,
    Lexeme,
    LexemeFusion,
    Morpheme,
    PartOfSpeech,
    Prefix,
    Rule,
    Scope,
    Scoped,
    Suffix,
    Tags,
)
from .errors import AffixDefinitionMissingForm, AffixDefinitionMissingVar


@dataclass(eq=True, frozen=True)
class TemplateName:
    name: str


Var = Literal["$"]  # todo: should var be just a string template?
VarFusion = Fusion[Var, Scoped[Prefix], Scoped[Suffix]]


@dataclass(eq=True, frozen=True)
class Template:
    name: TemplateName
    tags: Tags
    vars: tuple[VarFusion, ...]


@dataclass(eq=True, frozen=True)
class Entry:
    template: TemplateName | None
    tags: Tags
    lexeme: LexemeFusion
    form: Scoped[DefaultWord]
    part_of_speech: PartOfSpeech
    definition: str

    def description(self) -> str:
        return f"{self.part_of_speech} {self.definition}"


@dataclass(eq=True, frozen=True)
class AffixDefinition:
    stressed: bool
    tags: Tags
    affix: Affix
    era: Rule | None = field(default=None)
    form: Scoped[DefaultWord] | VarFusion | None = field(default=None)
    sources: tuple[Lexeme, ...] = field(
        default_factory=tuple
    )  # todo: or DefaultWord - can bare Morpheme appear?
    description: str = field(default="")

    def get_era(self) -> Rule | None:
        if self.era is not None:
            return self.era
        elif (
            isinstance(self.form, Scoped)
            and isinstance(self.form.scoped, Component)
            and isinstance(self.form.scoped.form, Fusion)
            and isinstance(self.form.scoped.form.stem, Morpheme)
        ):
            return self.form.scoped.form.stem.era
        else:
            return None

    def is_var(self) -> bool:
        return self.form is not None and isinstance(self.form, Fusion)

    def get_form(self) -> Scoped[DefaultWord]:
        if self.form is not None:
            assert isinstance(self.form, Scoped)
            return self.form
        elif self.sources:
            return Scoped(
                reduce(
                    lambda head, tail: Compound(head, Joiner.head(), tail),
                    map(
                        lambda source: cast(DefaultWord, Component(Fusion(source))),
                        self.sources,
                    ),
                )
            )
        else:
            raise AffixDefinitionMissingForm(self)

    def get_var(self) -> VarFusion:
        if self.form is not None and isinstance(self.form, Fusion):
            return self.form
        else:
            raise AffixDefinitionMissingVar(self)

    def to_entry(self) -> Entry:
        return Entry(
            None,
            self.tags,
            self.affix.to_fusion(),
            self.get_form(),
            PartOfSpeech("afx"),
            self.description,
        )

    def to_scoped_lexeme_fusion(self) -> Scoped[LexemeFusion]:
        return Scoped(self.affix.to_fusion(), self.tags.scope)


@dataclass(eq=True, frozen=True)
class ScopeDefinition:
    scope: Scope
    parent: Scope
    changes: Path = field(default=CHANGES_PATH)
