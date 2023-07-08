import re
from abc import ABCMeta, abstractmethod

from ...evolve.domain import Evolved
from .conlang_macro import ConlangMacro


class RawMacro(ConlangMacro, metaclass=ABCMeta):
    @classmethod
    def expression(cls) -> str:
        return rf"\b{cls.token()}\{{(?P<text>.+?)\}}"

    @classmethod
    @abstractmethod
    def token(cls) -> str:
        pass

    @abstractmethod
    def map_text(self, text: str) -> str:
        pass

    def map_match(self, match: re.Match[str]) -> str:
        return self.map_text(match.group("text"))


class RawEvolveMacro(RawMacro, metaclass=ABCMeta):
    def map_text(self, text: str) -> str:
        return " ".join(
            self.map_evolved(evolved) for evolved in self.translator.evolve_string(text)
        )

    @abstractmethod
    def map_evolved(self, evolved: Evolved) -> str:
        pass


class RawRomanizedMacro(RawEvolveMacro):
    @classmethod
    def token(cls) -> str:
        return "r"

    def map_evolved(self, evolved: Evolved) -> str:
        return evolved.modern


class RawPhoneticMacro(RawEvolveMacro):
    @classmethod
    def token(cls) -> str:
        return "ph"

    def map_evolved(self, evolved: Evolved) -> str:
        return evolved.phonetic


class RawProtoMacro(RawEvolveMacro):
    @classmethod
    def token(cls) -> str:
        return "pr"

    def map_evolved(self, evolved: Evolved) -> str:
        return evolved.proto


class RawDefinitionMacro(RawMacro):
    @classmethod
    def token(cls) -> str:
        return "d"

    def map_text(self, text: str) -> str:
        return "; ".join(self.translator.define_string(text))
