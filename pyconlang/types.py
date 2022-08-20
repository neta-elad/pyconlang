from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, List, Optional, Tuple, Union


@dataclass(eq=True, frozen=True)
class Rule:
    name: str


@dataclass(eq=True, frozen=True)
class Canonical:
    name: str


@dataclass(eq=True, frozen=True)
class Proto:
    form: str
    era: Optional[Rule]


@dataclass(eq=True, frozen=True)
class TemplateName:
    name: str


@dataclass(eq=True, frozen=True)
class PartOfSpeech:
    name: str


class AffixType(Enum):
    PREFIX = auto()
    SUFFIX = auto()


@dataclass(eq=True, frozen=True)
class Affix:
    name: str
    type: AffixType


@dataclass(eq=True, frozen=True)
class Fusion:
    stem: Canonical
    affixes: Tuple[Affix, ...]

    @classmethod
    def from_prefixes_and_suffixes(
        cls, prefixes: List[Affix], stem: Canonical, suffixes: List[Affix]
    ) -> "Fusion":
        return cls(stem, tuple(prefixes + suffixes))


Form = Union[Proto, Fusion]


@dataclass(eq=True, frozen=True)
class Entry:
    template: Optional[TemplateName]
    canonical: Canonical
    form: Form
    part_of_speech: PartOfSpeech
    definition: str


@dataclass(eq=True, frozen=True)
class AffixDefinition:
    stressed: bool
    affix: Affix
    era: Optional[Rule]
    form: Optional[Form]
    sources: Tuple[Canonical, ...]
    description: str

    def get_era(self) -> Optional[Rule]:
        if self.era is not None:
            return self.era
        elif isinstance(self.form, Proto):
            return self.form.era
        else:
            return None

    def get_form(self) -> Form:
        if self.form is not None:
            return self.form
        elif len(self.sources) == 1:
            return Fusion(self.sources[0], ())
        else:
            raise RuntimeError(f"Bad affix definition {self}")


@dataclass(eq=True, frozen=True)
class ResolvedForm:
    stem: Proto
    affixes: Tuple["ResolvedAffix", ...]


@dataclass(eq=True, frozen=True)
class ResolvedAffix:
    stressed: bool
    affix: Affix
    era: Optional[Rule]
    form: ResolvedForm


@dataclass(eq=True, frozen=True)
class Var:
    affixes: Tuple[Affix, ...]

    @classmethod
    def from_iterable(cls, iterable: Iterable[Affix]) -> "Var":
        return cls(tuple(iterable))


@dataclass(eq=True, frozen=True)
class Template:
    name: TemplateName
    vars: Tuple[Var, ...]

    @classmethod
    def from_args(cls, name: TemplateName, *var_args: Var) -> "Template":
        return cls(name, var_args)
