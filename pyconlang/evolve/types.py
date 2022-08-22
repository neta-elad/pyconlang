from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class Evolved:
    proto: str
    modern: str
    phonetic: str
