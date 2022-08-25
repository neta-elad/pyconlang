from inspect import cleandoc

from pyconlang.evolve.tracer import TraceLine, group_trace_lines, parse_trace_lines


def test_grouping():
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


def test_parser():
    assert (
        parse_trace_lines(
            cleandoc(
                """
                Applied rule1 to word1: a -> b
                Applied rule1 to word2: c -> d
                Applied rule2 to word2: d -> e
                Applied rule3 to word1: b -> f
                """
            )
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
