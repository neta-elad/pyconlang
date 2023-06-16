import abc
from dataclasses import dataclass, field
from enum import Enum, auto
from itertools import chain
from typing import List, Optional, Tuple, Union

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
    era: Optional[Rule] = field(default=None)

    def era_name(self) -> Optional[str]:
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

    def fuse(self, stem: str, affix: str, syllable_break: Optional[str] = None) -> str:
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
class Affix(abc.ABC):
    name: str

    @property
    @abc.abstractmethod
    def type(self) -> AffixType:
        ...  # todo: remvoe

    @abc.abstractmethod
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


Definable = Union[Lexeme, Prefix, Suffix]


@dataclass(eq=True, frozen=True)
class Var:
    prefixes: Tuple[Prefix, ...]
    """prefixes are stored in reversed order"""

    suffixes: Tuple[Suffix, ...]

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: List[Prefix], suffixes: List[Suffix]
    ) -> "Var":
        return cls(tuple(reversed(prefixes)), tuple(suffixes))

    def show(self, stem: str) -> str:
        for affix in self.prefixes + self.suffixes:
            stem = affix.type.fuse(stem, affix.name, ".")

        return stem

    def __str__(self) -> str:
        return self.show("$")


Describable = Union["Unit", Affix]


@dataclass(eq=True, frozen=True)
class Fusion:
    stem: "Unit"
    prefixes: Tuple[Prefix, ...] = field(default=())
    """prefixes are stored in reversed order"""

    suffixes: Tuple[Suffix, ...] = field(default=())

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: List[Prefix], stem: "Unit", suffixes: List[Suffix]
    ) -> "Fusion":
        return cls(stem, tuple(reversed(prefixes)), tuple(suffixes))

    def __str__(self) -> str:
        return (
            "".join(affix.name + "." for affix in self.prefixes)
            + str(self.stem)
            + "".join("." + affix.name for affix in self.suffixes)
        )


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
    era: Optional[Rule] = field(default=None)

    @classmethod
    def head(cls, era: Optional[Rule] = None) -> "Joiner":
        return cls(JoinerStress.HEAD, era)

    @classmethod
    def tail(cls, era: Optional[Rule] = None) -> "Joiner":
        return cls(JoinerStress.TAIL, era)

    def __str__(self) -> str:
        return f"{self.stress}{self.era or ''}"


@dataclass(eq=True, frozen=True)
class Compound:
    head: "Unit"
    joiner: Joiner
    tail: "Unit"

    @property
    def stress(self) -> JoinerStress:  # todo: remove
        return self.joiner.stress

    @property
    def era(self) -> Optional[Rule]:  # todo: remove
        return self.joiner.era

    def era_name(self) -> Optional[str]:
        if self.era is None:
            return None
        return self.era.name

    def __str__(self) -> str:
        return f"[{self.head} {self.joiner} {self.tail}]"


Unit = Union[Morpheme, Lexeme, Fusion, Compound]


@dataclass(eq=True, frozen=True)
class Entry:
    template: Optional[TemplateName]
    lexeme: Lexeme
    form: Unit
    part_of_speech: PartOfSpeech
    definition: str

    def description(self) -> str:
        return f"{self.part_of_speech} {self.definition}"


@dataclass(eq=True, frozen=True)
class AffixDefinition:
    stressed: bool
    affix: Affix
    era: Optional[Rule]
    form: Optional[Union[Unit, Var]]
    sources: Tuple[Lexeme, ...]  # or Form - can bare Proto appear?
    description: str

    def get_era(self) -> Optional[Rule]:
        if self.era is not None:
            return self.era
        elif isinstance(self.form, Fusion) and isinstance(self.form.stem, Morpheme):
            return self.form.stem.era
        else:
            return None

    def is_var(self) -> bool:
        return self.form is not None and isinstance(self.form, Var)

    def get_form(self) -> Unit:
        if self.form is not None and not isinstance(self.form, Var):
            return self.form
        elif len(self.sources) == 1:
            return self.sources[0]
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
    prefixes: Tuple["ResolvedAffix", ...] = field(default=())
    suffixes: Tuple["ResolvedAffix", ...] = field(default=())

    def extend_prefixes(self, *prefixes: "ResolvedAffix") -> "ResolvedForm":
        return ResolvedForm(self.stem, prefixes + self.prefixes, self.suffixes)

    def extend_suffixes(self, *suffixes: "ResolvedAffix") -> "ResolvedForm":
        return ResolvedForm(self.stem, self.prefixes, self.suffixes + suffixes)

    def extend(
        self,
        prefixes: Tuple["ResolvedAffix", ...],
        suffixes: Tuple["ResolvedAffix", ...],
    ) -> "ResolvedForm":
        return self.extend_prefixes(*prefixes).extend_suffixes(*suffixes)

    def extend_any(self, affix: "ResolvedAffix") -> "ResolvedForm":
        if affix.type is AffixType.PREFIX:
            return self.extend_prefixes(affix)
        else:
            return self.extend_suffixes(affix)

    def to_morphemes(self) -> List[Morpheme]:
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
    era: Optional[Rule]
    form: ResolvedForm

    @classmethod
    def from_compound(cls, compound: Compound, tail: ResolvedForm) -> "ResolvedAffix":
        return cls(
            compound.stress == JoinerStress.TAIL, AffixType.SUFFIX, compound.era, tail
        )

    def era_name(self) -> Optional[str]:
        if self.era is None:
            return None
        return self.era.name


@dataclass(eq=True, frozen=True)
class Template:
    name: TemplateName
    vars: Tuple[Var, ...]

    @classmethod
    def from_args(cls, name: TemplateName, *var_args: Var) -> "Template":
        return cls(name, var_args)
