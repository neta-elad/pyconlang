from abc import ABCMeta
from itertools import chain

from .advanced_macros import AdvancedMacro


class BatchingMacro(AdvancedMacro, metaclass=ABCMeta):
    batch: list[str] = []

    def run(self, lines: list[str]) -> list[str]:
        self.batch = []
        lines = super().run(lines)

        all_resolved = list(chain(*map(self.translator.resolve_string, self.batch)))
        self.translator.evolver.evolve(all_resolved)

        return lines

    def map_inner_text(self, text: str) -> str:
        self.batch.append(text.strip())
        return f"{self.token()}{{{text}}}"


class BatchingRomanizedMacro(BatchingMacro):
    @classmethod
    def token(cls) -> str:
        return "r"

    def map_inner_text(self, text: str) -> str:
        return f"**{super().map_inner_text(text)}**"


class BatchingPhoneticMacro(BatchingMacro):
    @classmethod
    def token(cls) -> str:
        return "ph"

    def map_inner_text(self, text: str) -> str:
        return rf"<ruby>r[{text}] <rt>\[{super().map_inner_text(text)}\]</rt></ruby>"
