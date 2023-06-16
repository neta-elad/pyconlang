import re
from xml.etree import ElementTree

from markdown import Markdown
from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension


class DelimitedProcessor(BlockProcessor):
    delimiter: str

    def __init__(self, parser: BlockParser, delimiter: str) -> None:
        super().__init__(parser)
        self.delimiter = delimiter

    def pattern(self) -> str:
        return rf"^\s*!{self.delimiter}\s*$"

    def test(self, parent: ElementTree.Element, block: str) -> bool:
        return re.match(self.pattern(), block) is not None

    def run(self, parent: ElementTree.Element, blocks: list[str]) -> bool:
        for i, block in enumerate(blocks[1:]):
            if not re.search(self.pattern(), block):
                continue

            self.run_inner_blocks(parent, blocks[1 : i + 1])

            for _j in range(0, i + 2):
                blocks.pop(0)
            return True
        return False

    def run_inner_blocks(self, parent: ElementTree.Element, blocks: list[str]) -> None:
        pass


class BoxedProcessor(DelimitedProcessor):
    def __init__(self, parser: BlockParser) -> None:
        super().__init__(parser, "boxed")

    def run_inner_blocks(self, parent: ElementTree.Element, blocks: list[str]) -> None:
        e = ElementTree.SubElement(parent, "div")
        e.set("class", "boxed")
        self.parser.parseBlocks(e, blocks)


class Boxed(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.parser.blockprocessors.register(BoxedProcessor(md.parser), "boxed", 50)


class DetailsProcessor(BlockProcessor):
    def __init__(self, parser: BlockParser) -> None:
        super().__init__(parser)

    def open_pattern(self) -> str:
        return r"^\s*!details:(.*)$"

    def close_pattern(self) -> str:
        return r"^\s*!details\s*$"

    def test(self, parent: ElementTree.Element, block: str) -> bool:
        return re.match(self.open_pattern(), block) is not None

    def run(self, parent: ElementTree.Element, blocks: list[str]) -> bool:
        for i, block in enumerate(blocks[1:]):
            if not re.search(self.close_pattern(), block):
                continue

            self.build_details(parent, blocks[0], blocks[1 : i + 1])

            for _j in range(0, i + 2):
                blocks.pop(0)
            return True
        return False

    def build_details(
        self, parent: ElementTree.Element, summary: str, blocks: list[str]
    ) -> None:
        details = ElementTree.SubElement(parent, "details")
        summary_element = ElementTree.SubElement(details, "summary")
        summary_element.text = self.clean_summary(summary)
        self.parser.parseBlocks(details, blocks)

    def clean_summary(self, summary: str) -> str:
        match = re.match(self.open_pattern(), summary)
        assert match is not None
        return match.group(1)


class Details(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.parser.blockprocessors.register(DetailsProcessor(md.parser), "details", 75)
