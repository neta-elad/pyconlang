import re
from abc import ABCMeta, abstractmethod

from markdown import Markdown
from markdown.preprocessors import Preprocessor

from ...translate import Translator


class ConlangMacro(Preprocessor, metaclass=ABCMeta):
    pattern: re.Pattern[str]
    translator: Translator

    def __init__(self, md: Markdown, translator: Translator) -> None:
        super().__init__(md)

        self.pattern = re.compile(self.expression())
        self.translator = translator

    @classmethod
    @abstractmethod
    def expression(cls) -> str:
        ...

    @abstractmethod
    def map_match(self, match: re.Match[str]) -> str:
        ...

    def run(self, lines: list[str]) -> list[str]:
        return [self.map_line(line) for line in lines]

    def map_line(self, line: str) -> str:
        return self.pattern.sub(self.map_match, line)
