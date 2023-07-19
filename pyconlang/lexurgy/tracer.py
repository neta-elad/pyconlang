from collections.abc import Iterable, Mapping

from .domain import TraceLine
from .parser import any_trace_line


def parse_trace_line(line: str) -> TraceLine | None:
    return any_trace_line.parse_or_raise(line)


def parse_trace_lines(
    lines: list[str], default: str = ""
) -> Mapping[str, list[TraceLine]]:
    return group_trace_lines(
        (trace for line in lines if (trace := parse_trace_line(line)) is not None),
        default,
    )


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
