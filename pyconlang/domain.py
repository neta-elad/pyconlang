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
class Scope:  # todo: rename to scope?
    scope: str = field(default="")

    def __str__(self) -> str:
        return f"%{self.scope}"


@dataclass(eq=True, frozen=True)
class Lexeme:
    name: str

    def __str__(self) -> str:
        return f"<{self.name}>"

    def scoped(self, scope: Scope | None = None) -> "Scoped[Lexeme]":
        return Scoped[Lexeme](self, scope)


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

    def to_fusion(self) -> "Fusion[Lexeme]":
        return Fusion(self.to_lexeme())

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


ScopedT = TypeVar("ScopedT", Lexeme, Affix)


@dataclass(eq=True, frozen=True)
class Scoped(Generic[ScopedT]):
    scoped: ScopedT
    scope: Scope | None = field(default=None)

    def __str__(self) -> str:
        return f"{self.scoped}{self.scope or ''}"


Definable = Lexeme | Affix  # todo: should be Scoped[Lexeme]

BaseUnit = Morpheme | Scoped[Lexeme]

Fusible = TypeVar("Fusible", Lexeme, BaseUnit, covariant=True)


@dataclass(eq=True, frozen=True)
class Fusion(Generic[Fusible]):
    stem: Fusible
    prefixes: tuple[Prefix, ...] = field(default=())
    """prefixes are stored in reversed order"""

    suffixes: tuple[Suffix, ...] = field(default=())

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: list[Prefix], stem: Fusible, suffixes: list[Suffix]
    ) -> "Fusion[Fusible]":
        return cls(stem, tuple(reversed(prefixes)), tuple(suffixes))

    def __str__(self) -> str:
        return (
            "".join(affix.name + "." for affix in self.prefixes)
            + str(self.stem)
            + "".join("." + affix.name for affix in self.suffixes)
        )


DefaultFusion = Fusion[BaseUnit]
LexemeFusion = Fusion[Lexeme]

Compoundable = TypeVar("Compoundable", DefaultFusion, Morpheme, covariant=True)


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

DefaultWord = Word[DefaultFusion]

# Unit = Morpheme | Lexeme | Fusion | Compound[Fusion]

Describable = Lexeme | Affix | Morpheme | Scoped[Lexeme]
Record = DefaultWord | DefaultFusion | Describable

ResolvedForm = Word[Morpheme]


@dataclass(eq=True, frozen=True)
class Tag:
    key: str
    value: str = field(default="")

    def __str__(self) -> str:
        if not self.value:
            return self.key
        return f"{self.key}:{self.value}"


@dataclass(eq=True, frozen=True)
class Tags:
    tags: frozenset[Tag] = field(default_factory=frozenset)

    @classmethod
    def from_set_and_scope(cls, tags: set[Tag], scope: Scope | None = None) -> Self:
        tags = set(tags)
        if scope is not None:
            scope_tag = Tag("scope", scope.scope)
            tags.add(scope_tag)
        return cls(frozenset(tags))

    def __post_init__(self) -> None:
        counter: Counter[str] = Counter()

        for tag in self.tags:
            counter[tag.key] += 1

        for key, value in counter.items():
            if value > 1:
                raise DoubleTagDefinition(key)

    @cached_property
    def map(self) -> dict[str, str]:
        return {tag.key: tag.value for tag in self.tags}

    @cached_property
    def scope(self) -> Scope:
        if "scope" in self.map:
            return Scope(self.map["scope"])

        return Scope(Metadata.default().scope)

    def __str__(self) -> str:
        return "{" + " ".join(str(tag) for tag in self.tags) + "}"


AnyWord = TypeVar("AnyWord", DefaultWord, Definable)


@dataclass
class Sentence(Generic[AnyWord]):
    tags: Tags
    words: list[AnyWord]

    @cached_property
    def scope(self) -> Scope:
        return self.tags.scope


DefaultSentence = Sentence[DefaultWord]
