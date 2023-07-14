from abc import ABCMeta

from .batching_macros import BatchingMacro


class BeforeAfterMacro(BatchingMacro, metaclass=ABCMeta):
    @classmethod
    def expression(cls) -> str:
        return rf"\B>{cls.token()}\[(?P<text>.+?)\]"

    def map_batched_text(self, text: str) -> str:
        return f"pr[{text}] \\> {self.token()}[{text}]"


class BeforeAfterRomanizedMacro(BeforeAfterMacro):
    @classmethod
    def token(cls) -> str:
        return "r"


class BeforeAfterPhoneticMacro(BeforeAfterMacro):
    @classmethod
    def token(cls) -> str:
        return "ph"


class AfterBeforeMacro(BatchingMacro, metaclass=ABCMeta):
    @classmethod
    def expression(cls) -> str:
        return rf"\b{cls.token()}<\[(?P<text>.+?)\]"

    def map_batched_text(self, text: str) -> str:
        return f"{self.token()}[{text}] \\< pr[{text}]"


class AfterBeforeRomanizedMacro(AfterBeforeMacro):
    @classmethod
    def token(cls) -> str:
        return "r"


class AfterBeforePhoneticMacro(AfterBeforeMacro):
    @classmethod
    def token(cls) -> str:
        return "ph"
