from dataclasses import dataclass, field
from enum import Enum, auto
from itertools import chain
from typing import Iterable, List, Optional, Tuple, Union

from .errors import AffixDefinitionMissingForm, AffixDefinitionMissingVar
from .metadata import Metadata


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
class Affix:
    name: str
    type: AffixType

    def __str__(self) -> str:
        return self.type.fuse("", self.name, ".")


@dataclass(eq=True, frozen=True)
class Var:
    affixes: Tuple[Affix, ...]

    @classmethod
    def from_iterable(cls, iterable: Iterable[Affix]) -> "Var":
        return cls(tuple(iterable))


Describable = Union["Unit", Affix]


@dataclass(eq=True, frozen=True)
class Fusion:
    stem: "Unit"
    affixes: Tuple[Affix, ...] = field(default=())

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: List[Affix], stem: "Unit", suffixes: List[Affix]
    ) -> "Fusion":
        return cls(stem, tuple(list(reversed(prefixes)) + suffixes))

    @classmethod
    def from_form(cls, form: "Unit") -> "Fusion":
        match form:
            case Fusion():
                return form
            case _:
                return Fusion(form)

    def __str__(self) -> str:
        return (
            "".join(
                affix.name + "."
                for affix in self.affixes
                if affix.type == AffixType.PREFIX
            )
            + str(self.stem)
            + "".join(
                "." + affix.name
                for affix in self.affixes
                if affix.type == AffixType.SUFFIX
            )
        )


class CompoundStress(Enum):
    HEAD = auto()
    TAIL = auto()

    def __str__(self) -> str:
        match self:
            case CompoundStress.HEAD:
                return "!+"
            case CompoundStress.TAIL:
                return "+!"


@dataclass(eq=True, frozen=True)
class Compound:
    head: "Unit"
    stress: CompoundStress
    era: Optional[Rule]
    tail: "Unit"

    def era_name(self) -> Optional[str]:
        if self.era is None:
            return None
        return self.era.name

    def __str__(self) -> str:
        return f"[{self.head} {self.stress}{self.era_name() or ''} {self.tail}]"


Unit = Union[Morpheme, Lexeme, Fusion, Compound]


@dataclass(eq=True, frozen=True)
class Entry:
    template: Optional[TemplateName]
    lexeme: Lexeme
    form: Compound
    part_of_speech: PartOfSpeech
    definition: str


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
        elif isinstance(self.form, Morpheme):
            return self.form.era
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
    affixes: Tuple["ResolvedAffix", ...] = field(default=())

    def extend(self, *affixes: "ResolvedAffix") -> "ResolvedForm":
        return ResolvedForm(self.stem, self.affixes + affixes)

    def to_morphemes(self) -> List[Morpheme]:
        morphemes = [[self.stem]]
        for affix in self.affixes:
            if affix.type is AffixType.PREFIX:
                morphemes.insert(0, affix.form.to_morphemes())
            else:
                morphemes.append(affix.form.to_morphemes())

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
            compound.stress == CompoundStress.TAIL, AffixType.SUFFIX, compound.era, tail
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
