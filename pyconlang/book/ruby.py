import re
from typing import Any
from xml.etree import ElementTree

from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor


class Ruby(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.inlinePatterns.register(
            RubyProcessor(),
            "ruby",
            1,
        )


class RubyProcessor(InlineProcessor):
    def __init__(self) -> None:
        super().__init__(r"()%(?P<text>[^%]+)%(?P<title>[^%]+)%")

    # InlineProcessor and its parent Pattern
    # have contradictory type annotations,
    # so we have to ignore type.
    def handleMatch(  # type: ignore
        self, m: re.Match[str], data: Any
    ) -> tuple[ElementTree.Element, int, int]:
        ruby = ElementTree.Element("ruby")
        ruby.text = m.group("text").strip() + " "
        title = ElementTree.Element("rt")
        title.text = m.group("title")
        ruby.append(title)
        return ruby, m.start(0), m.end(0)
