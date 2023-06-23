from collections.abc import Iterable, Mapping

from .domain import TraceLine
from .parser import trace_lines


def parse_trace_lines(string: str, default: str = "") -> Mapping[str, list[TraceLine]]:
    return group_trace_lines(trace_lines.parse_string(string, parse_all=True), default)


def group_trace_lines(
    lines: Iterable[TraceLine], default: str = ""
) -> Mapping[str, list[TraceLine]]:
    result: dict[str, list[TraceLine]] = {}
    for line in lines:
        if line.before == line.after:
            continue

        if not line.word and default:
            line = line.set_word(default)
        result.setdefault(line.word, [])
        result[line.word].append(line)

    return result
