from xml.etree import ElementTree

from markdown import Extension, Markdown
from markdown.treeprocessors import Treeprocessor


class SpanTable(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.treeprocessors.register(SpanTableProcessor(), "span_table", 100)


class SpanTableProcessor(Treeprocessor):
    def run(self, root: ElementTree.Element) -> ElementTree.Element | None:
        delete_cells: set[tuple[ElementTree.Element, ElementTree.Element]] = set()
        column_spans: dict[ElementTree.Element, int] = {}
        above_cells: dict[ElementTree.Element, ElementTree.Element] = {}
        row_spans: dict[ElementTree.Element, int] = {}
        for table in root.findall(".//table"):
            last_row = None
            for tr in table.findall(".//tr"):
                last_cell = None
                for i, cell in enumerate(tr):
                    if span_column(cell):
                        if last_cell is None:
                            raise RuntimeError(
                                "Cannot span column before any content cell"
                            )

                        column_spans.setdefault(last_cell, 1)
                        column_spans[last_cell] += 1
                        delete_cells.add((tr, cell))
                    elif span_row(cell):
                        if last_row is None or last_row[i] in delete_cells:
                            raise RuntimeError(
                                "Cannot span row before any content cell"
                            )

                        above_cells.setdefault(last_row[i], last_row[i])
                        above_cell = above_cells[last_row[i]]
                        above_cells[cell] = above_cell
                        row_spans.setdefault(above_cell, 1)
                        row_spans[above_cell] += 1
                        delete_cells.add((tr, cell))
                        last_cell = cell
                    else:
                        last_cell = cell

                last_row = tr

        for cell, colspan in column_spans.items():
            cell.set("colspan", str(colspan))

        for cell, rowspan in row_spans.items():
            cell.set("rowspan", str(rowspan))

        for tr, cell in delete_cells:
            tr.remove(cell)

        return None


def span_column(cell: ElementTree.Element) -> bool:
    return cell.text is not None and cell.text.strip() == "<"


def span_row(cell: ElementTree.Element) -> bool:
    return cell.text is not None and cell.text.strip() == "^"
