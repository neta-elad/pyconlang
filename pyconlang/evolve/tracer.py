from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

from pyparsing import ParserElement, Suppress, Word, pyparsing_unicode

from ..parser import tokens_map


@dataclass(eq=True, frozen=True)
class TraceLine:
    rule: str
    word: str
    before: str
    after: str


ParserElement.set_default_whitespace_chars(" \t")

word = Word(pyparsing_unicode.BasicMultilingualPlane.printables, exclude_chars=":")

trace_line = (
    Suppress("Applied")
    + word
    + Suppress("to")
    + word
    + Suppress(":")
    + word
    + Suppress("->")
    + word
    + Suppress("\n")[...]
).set_parse_action(tokens_map(TraceLine))


trace_lines = trace_line[...]


def parse_trace_lines(string: str) -> Mapping[str, List[TraceLine]]:
    return group_trace_lines(trace_lines.parse_string(string, parse_all=True))


def group_trace_lines(lines: Iterable[TraceLine]) -> Mapping[str, List[TraceLine]]:
    result: Dict[str, List[TraceLine]] = {}
    for line in lines:
        result.setdefault(line.word, [])
        result[line.word].append(line)

    return result
