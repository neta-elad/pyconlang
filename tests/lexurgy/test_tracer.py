from inspect import cleandoc

from pyconlang.lexurgy.domain import TraceLine
from pyconlang.lexurgy.parser import any_trace_line, trace_line, trace_line_heading
from pyconlang.lexurgy.tracer import group_trace_lines, parse_trace_lines

from ..test_old_parser import parse


def test_grouping() -> None:
    assert group_trace_lines(
        [
            TraceLine("rule1", "", "a", "b"),
        ],
        "word1",
    ) == {
        "word1": [
            TraceLine("rule1", "word1", "a", "b"),
        ]
    }

    assert group_trace_lines(
        [
            TraceLine("rule1", "word1", "a", "b"),
            TraceLine("rule1", "word2", "c", "d"),
            TraceLine("rule2", "word2", "d", "e"),
            TraceLine("rule3", "word1", "b", "f"),
        ]
    ) == {
        "word1": [
            TraceLine("rule1", "word1", "a", "b"),
            TraceLine("rule3", "word1", "b", "f"),
        ],
        "word2": [
            TraceLine("rule1", "word2", "c", "d"),
            TraceLine("rule2", "word2", "d", "e"),
        ],
    }


def test_parser() -> None:
    assert parse(trace_line_heading, "Tracing word1, word2") is None
    assert parse(trace_line, "Applied rule1 to word1: a -> b") == TraceLine(
        "rule1", "word1", "a", "b"
    )
    assert parse(any_trace_line, "Tracing word1, word2") is None
    assert parse(any_trace_line, "Applied rule1 to word1: a -> b") == TraceLine(
        "rule1", "word1", "a", "b"
    )


def test_parse_and_grouping() -> None:
    assert (
        parse_trace_lines(
            cleandoc(
                """
                Tracing word1, word2
                Applied rule1 to word1: a -> b
                Applied rule1 to word2: c -> d
                Applied rule2 to word2: d -> e
                Applied rule3 to word1: b -> f
                """
            ).splitlines()
        )
        == {
            "word1": [
                TraceLine("rule1", "word1", "a", "b"),
                TraceLine("rule3", "word1", "b", "f"),
            ],
            "word2": [
                TraceLine("rule1", "word2", "c", "d"),
                TraceLine("rule2", "word2", "d", "e"),
            ],
        }
    )
