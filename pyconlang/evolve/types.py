from dataclasses import dataclass, field
from typing import Optional, Tuple

from unidecode import unidecode

from ..types import AffixType, Morpheme, Rule


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
    affixes: Tuple["ArrangedAffix", ...] = field(default=())


@dataclass(eq=True, frozen=True)
class ArrangedAffix:
    stressed: bool
    type: AffixType
    era: Optional[Rule]
    form: ArrangedForm

    def era_name(self) -> Optional[str]:
        if self.era is None:
            return None
        return self.era.name
