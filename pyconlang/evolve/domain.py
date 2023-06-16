from dataclasses import dataclass, field

from unidecode import unidecode

from ..domain import AffixType, Morpheme, Rule


@dataclass(eq=True, frozen=True)
class Evolved:
    proto: str
    modern: str
    phonetic: str

    @property
    def simple(self) -> str:
        return unidecode(self.modern)


@dataclass(eq=True, frozen=True)
class ArrangedForm:
    stem: Morpheme
    affixes: tuple["ArrangedAffix", ...] = field(default=())


@dataclass(eq=True, frozen=True)
class ArrangedAffix:
    stressed: bool
    type: AffixType
    era: Rule | None
    form: ArrangedForm

    def era_name(self) -> str | None:
        if self.era is None:
            return None
        return self.era.name
