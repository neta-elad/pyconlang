from dataclasses import dataclass

from unidecode import unidecode


@dataclass(eq=True, frozen=True)
class Evolved:
    proto: str
    modern: str
    phonetic: str

    @property
    def simple(self) -> str:
        return unidecode(self.modern)
