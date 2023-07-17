from abc import ABCMeta, abstractmethod

from .advanced_macros import AdvancedMacro


class BatchingMacro(AdvancedMacro, metaclass=ABCMeta):
    batch: list[str] = []

    def run(self, lines: list[str]) -> list[str]:
        self.batch = []
        lines = super().run(lines)

        self.translator.resolve_and_evolve_all(self.batch)

        return lines

    def map_inner_text(self, text: str) -> str:
        self.batch.append(text.strip())
        return self.map_batched_text(text)

    @abstractmethod
    def map_batched_text(self, text: str) -> str:
        ...


class BatchingRomanizedMacro(BatchingMacro):
    @classmethod
    def token(cls) -> str:
        return "r"

    def map_batched_text(self, text: str) -> str:
        return f"**r({text})**"


class BatchingPhoneticMacro(BatchingMacro):
    @classmethod
    def token(cls) -> str:
        return "ph"

    def map_batched_text(self, text: str) -> str:
        return rf"<ruby>r[{text}] <rt>\[ph({text})\]</rt></ruby>"
