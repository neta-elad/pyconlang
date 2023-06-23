from pyparsing import ParserElement, Suppress, Word, pyparsing_unicode, rest_of_line

from ..parser import explicit_opt, tokens_map
from .domain import TraceLine

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
