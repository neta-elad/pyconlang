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
