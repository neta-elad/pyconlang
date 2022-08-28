from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

from pyparsing import ParserElement, Suppress, Word, pyparsing_unicode, rest_of_line

from ..parser import explicit_opt, tokens_map


@dataclass(eq=True, frozen=True)
class TraceLine:
    rule: str
    word: str
    before: str
    after: str

    def set_word(self, new_word: str) -> "TraceLine":
        return TraceLine(self.rule, new_word, self.before, self.after)


ParserElement.set_default_whitespace_chars(" \t")

word = Word(pyparsing_unicode.BasicMultilingualPlane.printables, exclude_chars=":")

to = explicit_opt(Suppress("to") - word, "")

trace_line = (
    Suppress("Applied")
    - word
    - to
    - Suppress(":")
    - word
    - Suppress("->")
    - word
    - Suppress("\n")[...]
).set_parse_action(tokens_map(TraceLine))

trace_line_heading = Word("Tracing") - rest_of_line - Suppress("\n")


trace_lines = Suppress(trace_line_heading) - trace_line[...]


def parse_trace_lines(string: str, default: str = "") -> Mapping[str, List[TraceLine]]:
    return group_trace_lines(trace_lines.parse_string(string, parse_all=True), default)


def group_trace_lines(
    lines: Iterable[TraceLine], default: str = ""
) -> Mapping[str, List[TraceLine]]:
    result: Dict[str, List[TraceLine]] = {}
    for line in lines:
        if not line.word and default:
            line = line.set_word(default)
        result.setdefault(line.word, [])
        result[line.word].append(line)

    return result
