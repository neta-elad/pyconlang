from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import reduce
from typing import Generic, TypeVar, cast

from .errors import AffixDefinitionMissingForm, AffixDefinitionMissingVar
from .unicode import combine


@dataclass(eq=True, frozen=True)
class Rule:
    name: str

    def __str__(self) -> str:
        return f"@{self.name}"


@dataclass(eq=True, frozen=True)
class Lexeme:
    name: str

    def __str__(self) -> str:
        return f"<{self.name}>"


@dataclass(eq=True, frozen=True)
class Morpheme:
    form: str
    era: Rule | None = field(default=None)

    def era_name(self) -> str | None:
        if self.era is None:
            return None
        return self.era.name

    def __str__(self) -> str:
        return f"*{self.form}{self.era or ''}"


@dataclass(eq=True, frozen=True)
class TemplateName:
    name: str


@dataclass(eq=True, frozen=True)
class PartOfSpeech:
    name: str

    def __str__(self) -> str:
        return f"({self.name}.)"


@dataclass(eq=True, frozen=True)
class AffixBase(ABC):
    name: str

    @abstractmethod
    def combine(self, stem: str, name: str) -> str:
        ...

    def to_lexeme(self) -> Lexeme:
        return Lexeme(str(self))

    def __str__(self) -> str:
        return self.combine("", self.name)


@dataclass(eq=True, frozen=True)
class Prefix(AffixBase):
    def combine(self, stem: str, name: str) -> str:
        return combine(name, stem, ".")


@dataclass(eq=True, frozen=True)
class Suffix(AffixBase):
    def combine(self, stem: str, name: str) -> str:
        return combine(stem, name, ".")


Affix = Prefix | Suffix

Definable = Lexeme | Affix


@dataclass(eq=True, frozen=True)
class Var:
    prefixes: tuple[Prefix, ...]
    """prefixes are stored in reversed order"""

    suffixes: tuple[Suffix, ...]

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
class Fusion:
    stem: "Unit"
    prefixes: tuple[Prefix, ...] = field(default=())
    """prefixes are stored in reversed order"""

    suffixes: tuple[Suffix, ...] = field(default=())

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: list[Prefix], stem: "Unit", suffixes: list[Suffix]
    ) -> "Fusion":
        return cls(stem, tuple(reversed(prefixes)), tuple(suffixes))

    def __str__(self) -> str:
        return (
            "".join(affix.name + "." for affix in self.prefixes)
            + str(self.stem)
            + "".join("." + affix.name for affix in self.suffixes)
        )


Compoundable = TypeVar("Compoundable", Morpheme, Fusion)


class Tree(Generic[Compoundable], metaclass=ABCMeta):
    @abstractmethod
    def leaves(self) -> list[Compoundable]:
        ...


@dataclass(eq=True, frozen=True)
class Component(Tree[Compoundable]):
    form: Compoundable

    def __str__(self) -> str:
        return str(self.form)

    def leaves(self) -> list[Compoundable]:
        return [self.form]


class JoinerStress(Enum):
    HEAD = auto()
    TAIL = auto()

    def __str__(self) -> str:
        match self:
            case JoinerStress.HEAD:
                return "!+"
            case JoinerStress.TAIL:
                return "+!"


@dataclass(eq=True, frozen=True)
class Joiner:
    stress: JoinerStress
    era: Rule | None = field(default=None)

    @classmethod
    def head(cls, era: Rule | None = None) -> "Joiner":
        return cls(JoinerStress.HEAD, era)

    @classmethod
    def tail(cls, era: Rule | None = None) -> "Joiner":
        return cls(JoinerStress.TAIL, era)

    def __str__(self) -> str:
        return f"{self.stress}{self.era or ''}"

    def era_name(self) -> str | None:
        if self.era is None:
            return None
        return self.era.name


@dataclass(eq=True, frozen=True)
class Compound(Tree[Compoundable]):
    head: "Word[Compoundable]"
    joiner: Joiner
    tail: "Word[Compoundable]"

    def __str__(self) -> str:
        return f"[{self.head} {self.joiner} {self.tail}]"

    def leaves(self) -> list[Compoundable]:
        return self.head.leaves() + self.tail.leaves()


Word = Component[Compoundable] | Compound[Compoundable]


Unit = Morpheme | Lexeme | Fusion | Compound[Fusion]


Describable = Lexeme | Affix | Morpheme
Record = Word[Fusion] | Fusion | Describable


@dataclass(eq=True, frozen=True)
class Entry:
    template: TemplateName | None
    lexeme: Lexeme
    form: Word[Fusion]
    part_of_speech: PartOfSpeech
    definition: str

    def description(self) -> str:
        return f"{self.part_of_speech} {self.definition}"


@dataclass(eq=True, frozen=True)
class AffixDefinition:
    stressed: bool
    affix: Affix
    era: Rule | None
    form: Word[Fusion] | Var | None
    sources: tuple[Lexeme, ...]  # or Form - can bare Proto appear?
    description: str

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
            self.get_form(),
            PartOfSpeech("afx"),
            self.description,
        )


ResolvedForm = Word[Morpheme]


@dataclass(eq=True, frozen=True)
class Template:
    name: TemplateName
    vars: tuple[Var, ...]

    @classmethod
    def from_args(cls, name: TemplateName, *var_args: Var) -> "Template":
        return cls(name, var_args)
