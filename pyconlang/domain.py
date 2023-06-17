from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from itertools import chain
from typing import Generic, TypeVar

from .errors import AffixDefinitionMissingForm, AffixDefinitionMissingVar
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
class TemplateName:
    name: str


@dataclass(eq=True, frozen=True)
class PartOfSpeech:
    name: str

    def __str__(self) -> str:
        return f"({self.name}.)"


class AffixType(Enum):
    PREFIX = auto()
    SUFFIX = auto()

    def fuse(self, stem: str, affix: str, syllable_break: str | None = None) -> str:
        if syllable_break is None:
            syllable_break = self.syllable_break()

        match self:
            case AffixType.PREFIX:
                return affix + syllable_break + stem
            case AffixType.SUFFIX:
                return stem + syllable_break + affix

    @staticmethod
    def syllable_break() -> str:
        if Metadata.default().syllables:
            return "."
        else:
            return ""


@dataclass(eq=True, frozen=True)
class Affix(ABC):
    name: str

    @property
    @abstractmethod
    def type(self) -> AffixType:
        ...  # todo: remvoe

    @abstractmethod
    def __str__(self) -> str:
        ...


@dataclass(eq=True, frozen=True)
class Prefix(Affix):
    @property
    def type(self) -> AffixType:  # todo: remove
        return AffixType.PREFIX

    def __str__(self) -> str:
        return combine(self.name, "", ".")


@dataclass(eq=True, frozen=True)
class Suffix(Affix):
    @property
    def type(self) -> AffixType:  # todo: remove
        return AffixType.SUFFIX

    def __str__(self) -> str:
        return combine("", self.name, ".")


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
            stem = affix.type.fuse(stem, affix.name, ".")

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


@dataclass(eq=True, frozen=True)
class Component(Generic[Compoundable]):
    form: Compoundable

    def __str__(self) -> str:
        return str(self.form)


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


@dataclass(eq=True, frozen=True)
class Compound(Generic[Compoundable]):
    head: "Word[Compoundable]"
    joiner: Joiner
    tail: "Word[Compoundable]"

    @property
    def stress(self) -> JoinerStress:  # todo: remove
        return self.joiner.stress

    @property
    def era(self) -> Rule | None:  # todo: remove
        return self.joiner.era

    def era_name(self) -> str | None:
        if self.era is None:
            return None
        return self.era.name

    def __str__(self) -> str:
        return f"[{self.head} {self.joiner} {self.tail}]"


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
        elif len(self.sources) == 1:
            return Component(Fusion(self.sources[0]))
        else:
            raise AffixDefinitionMissingForm(self)

    def get_var(self) -> Var:
        if self.form is not None and isinstance(self.form, Var):
            return self.form
        else:
            raise AffixDefinitionMissingVar(self)


@dataclass(eq=True, frozen=True)
class ResolvedForm:
    stem: Morpheme
    prefixes: tuple["ResolvedAffix", ...] = field(default=())
    suffixes: tuple["ResolvedAffix", ...] = field(default=())

    def extend_prefixes(self, *prefixes: "ResolvedAffix") -> "ResolvedForm":
        return ResolvedForm(self.stem, prefixes + self.prefixes, self.suffixes)

    def extend_suffixes(self, *suffixes: "ResolvedAffix") -> "ResolvedForm":
        return ResolvedForm(self.stem, self.prefixes, self.suffixes + suffixes)

    def extend(
        self,
        prefixes: tuple["ResolvedAffix", ...],
        suffixes: tuple["ResolvedAffix", ...],
    ) -> "ResolvedForm":
        return self.extend_prefixes(*prefixes).extend_suffixes(*suffixes)

    def extend_any(self, affix: "ResolvedAffix") -> "ResolvedForm":
        if affix.type is AffixType.PREFIX:
            return self.extend_prefixes(affix)
        else:
            return self.extend_suffixes(affix)

    def to_morphemes(self) -> list[Morpheme]:
        morphemes = (
            [prefix.form.to_morphemes() for prefix in self.prefixes]
            + [[self.stem]]
            + [suffix.form.to_morphemes() for suffix in self.suffixes]
        )

        return list(chain(*morphemes))


@dataclass(eq=True, frozen=True)
class ResolvedAffix:
    stressed: bool
    type: AffixType
    era: Rule | None
    form: ResolvedForm

    @classmethod
    def from_compound(
        cls, compound: Compound[Fusion], tail: ResolvedForm
    ) -> "ResolvedAffix":
        return cls(
            compound.stress == JoinerStress.TAIL, AffixType.SUFFIX, compound.era, tail
        )

    def era_name(self) -> str | None:
        if self.era is None:
            return None
        return self.era.name


@dataclass(eq=True, frozen=True)
class Template:
    name: TemplateName
    vars: tuple[Var, ...]

    @classmethod
    def from_args(cls, name: TemplateName, *var_args: Var) -> "Template":
        return cls(name, var_args)


T = TypeVar("T")


@dataclass(eq=True, frozen=True)
class BranchJoin(Generic[T]):
    head: "JoinTree[T]"
    joiner: Joiner
    tail: "JoinTree[T]"

    @property
    def stress(self) -> JoinerStress:  # todo: remove
        return self.joiner.stress

    @property
    def era(self) -> Rule | None:  # todo: remove
        return self.joiner.era

    def era_name(self) -> str | None:
        if self.era is None:
            return None
        return self.era.name

    def __str__(self) -> str:
        return f"[{self.head} {self.joiner} {self.tail}]"


@dataclass(eq=True, frozen=True)
class LeafJoin(Generic[T]):
    value: T

    def __str__(self) -> str:
        return f"[{self.value}]"


JoinTree = LeafJoin[T] | BranchJoin[T]
