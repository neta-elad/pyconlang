import re
from typing import Any
from xml.etree import ElementTree

from markdown import Markdown
from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.extensions.attr_list import AttrListTreeprocessor
from markdown.inlinepatterns import InlineProcessor


class MultiInlineProcessor(InlineProcessor):
    def __init__(self, pattern: str) -> None:
        super().__init__(pattern)

    # InlineProcessor and its parent Pattern
    # have contradictory type annotations,
    # so we have to ignore type.
    def handleMatch(  # type: ignore
        self, m: re.Match[str], data: Any
    ) -> tuple[ElementTree.Element, int, int]:
        el = ElementTree.Element("span")
        el.text = m.group(2)
        return el, m.start(0), m.end(0)


class MultiBlockProcessor(BlockProcessor):
    token: str
    attr_list: AttrListTreeprocessor

    def __init__(self, parser: BlockParser, token: str) -> None:
        super().__init__(parser)
        self.token = token
        self.attr_list = AttrListTreeprocessor(self.parser.md)

    def open_pattern(self) -> str:
        return rf"^\s*&{self.token}\{{\s*$"

    def close_pattern(self) -> str:
        return r"^\s*\}({:(.*)})?$"

    def test(self, parent: ElementTree.Element, block: str) -> bool:
        return re.match(self.open_pattern(), block) is not None

    def run(self, parent: ElementTree.Element, blocks: list[str]) -> bool:
        for i, block in enumerate(blocks[1:]):
            match = re.match(self.close_pattern(), block)
            if match is None:
                continue

            last_block = match.group(2)
            e = self.run_inner_blocks(parent, blocks[1 : i + 1])

            if last_block is not None:
                self.attr_list.assign_attrs(e, last_block)

            for _j in range(0, i + 2):
                blocks.pop(0)
            return True
        return False

    def run_inner_blocks(
        self, parent: ElementTree.Element, blocks: list[str]
    ) -> ElementTree.Element:
        container = ElementTree.SubElement(parent, "div")
        self.parser.parseBlocks(container, blocks)
        return container


class MultiExtension(Extension):
    def __init__(self, token: str) -> None:
        super().__init__()

        self.token = token

    def extendMarkdown(self, md: Markdown) -> None:
        md.inlinePatterns.register(
            MultiInlineProcessor(rf"()&{self.token}\{{(.*?)\}}"),
            f"multi-inline-{self.token}",
            50,
        )
        md.parser.blockprocessors.register(
            MultiBlockProcessor(md.parser, self.token),
            f"multi-inline-block-{self.token}",
            50,
        )
