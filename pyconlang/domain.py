from abc import ABC, ABCMeta, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import cached_property
from typing import Generic, Self, TypeVar

from .errors import DoubleTagDefinition
from .metadata import Metadata
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
        return f'"{self.head} {self.joiner} {self.tail}"'

    def leaves(self) -> list[Compoundable]:
        return self.head.leaves() + self.tail.leaves()


Word = Component[Compoundable] | Compound[Compoundable]

Unit = Morpheme | Lexeme | Fusion | Compound[Fusion]

Describable = Lexeme | Affix | Morpheme
Record = Word[Fusion] | Fusion | Describable

ResolvedForm = Word[Morpheme]


@dataclass(eq=True, frozen=True)
class Lang:
    lang: str | None = field(default=None)

    def __str__(self) -> str:
        if self.lang is None:
            return ""

        return f"%{self.lang}"


@dataclass(eq=True, frozen=True)
class Tag:
    key: str
    value: str | None = field(default=None)

    def __str__(self) -> str:
        if self.value is None:
            return self.key
        return f"{self.key}:{self.value}"


@dataclass(eq=True, frozen=True)
class Tags:
    tags: frozenset[Tag] = field(default_factory=frozenset)

    @classmethod
    def from_set_and_lang(cls, tags: set[Tag], lang: Lang | None = None) -> Self:
        tags = set(tags)
        if lang is not None:
            lang_tag = Tag("lang", lang.lang)
            tags.add(lang_tag)
        return cls(frozenset(tags))

    def __post_init__(self) -> None:
        counter: Counter[str] = Counter()

        for tag in self.tags:
            counter[tag.key] += 1

        for key, value in counter.items():
            if value > 1:
                raise DoubleTagDefinition(key)

    @cached_property
    def map(self) -> dict[str, str | None]:
        return {tag.key: tag.value for tag in self.tags}

    @cached_property
    def lang(self) -> Lang:
        if "lang" in self.map:
            return Lang(self.map["lang"])

        return Lang(Metadata.default().lang)

    def __str__(self) -> str:
        return "{" + " ".join(str(tag) for tag in self.tags) + "}"


AnyWord = TypeVar("AnyWord", Word[Fusion], Definable)


@dataclass
class Sentence(Generic[AnyWord]):
    tags: Tags
    words: list[AnyWord]

    @cached_property
    def lang(self) -> Lang:
        return self.tags.lang
