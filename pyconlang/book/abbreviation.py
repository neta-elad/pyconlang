from re import Match
from typing import Any
from xml.etree import ElementTree

from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor


class Abbreviation(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.inlinePatterns.register(
            AbbreviationProcessor(),
            "abbreviation",
            1,
        )


class AbbreviationProcessor(InlineProcessor):
    def __init__(self) -> None:
        super().__init__(r"()\+(?P<abbr>[^+]+)\+(?P<title>[^+]+)\+")

    # InlineProcessor and its parent Pattern
    # have contradictory type annotations,
    # so we have to ignore type.
    def handleMatch(  # type: ignore
        self, m: Match[str], data: Any
    ) -> tuple[ElementTree.Element, int, int]:
        abbr = ElementTree.Element("abbr")
        abbr.text = m.group("abbr")
        abbr.set("title", m.group("title"))
        return abbr, m.start(0), m.end(0)
