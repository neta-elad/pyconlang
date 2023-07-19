from pyparsing import Suppress, Word, pyparsing_unicode, rest_of_line, token_map

from ..old_parser import explicit_opt, tokens_map
from .domain import TraceLine

# ParserElement.set_default_whitespace_chars(" \t")

word = Word(pyparsing_unicode.BasicMultilingualPlane.printables, exclude_chars=":")
to = explicit_opt(Suppress("to") - word, "")
trace_line = (
    Suppress("Applied") - word - to - Suppress(":") - word - Suppress("->") - word
).set_parse_action(tokens_map(TraceLine))
trace_line_heading = (Suppress("Tracing") - rest_of_line).set_parse_action(
    token_map(lambda _: None)
)

any_trace_line = trace_line_heading ^ trace_line

# trace_lines = Suppress(trace_line_heading) - trace_line[...]
