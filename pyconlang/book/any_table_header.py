from typing import Optional
from xml.etree import ElementTree

from markdown import Extension, Markdown
from markdown.treeprocessors import Treeprocessor


class AnyTableHeader(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.treeprocessors.register(AnyTableHeaderProcessor(), "any_table_header", 90)


class AnyTableHeaderProcessor(Treeprocessor):
    def run(self, root: ElementTree.Element) -> Optional[ElementTree.Element]:
        for table in root.findall(".//table"):
            for tr in table.findall(".//tr"):
                for cell in tr:
                    if table_header(cell):
                        assert cell.text is not None
                        cell.text = cell.text.strip()[:-1]
                        cell.tag = "th"

        return None


def table_header(cell: ElementTree.Element) -> bool:
    return cell.text is not None and cell.text.strip().endswith(">")
