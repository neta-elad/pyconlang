import pytest

from pyconlang.evolve.batch import (
    LeafEvolveQuery,
    NodeEvolveQuery,
    build_and_order,
    build_query,
    order_in_layers,
)
from pyconlang.evolve.errors import BadAffixation
from pyconlang.types import AffixType, Proto, ResolvedAffix, ResolvedForm, Rule


def test_one_node():
    a = ResolvedForm(Proto("a"))
    assert build_query(a) == LeafEvolveQuery("a")

    a = ResolvedForm(Proto("a", Rule("1")))
    assert build_query(a) == LeafEvolveQuery("a", start="1")


def test_two_nodes_same():
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))

    assert build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")
    )

    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )

    assert build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )


def test_two_nodes_different():
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )

    assert build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )

    with pytest.raises(BadAffixation):
        a = ResolvedForm(Proto("a", Rule("1")))
        b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))

        build_query(a.extend(b))

    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("b", Rule("2")))
    )
    assert build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="2"),
        LeafEvolveQuery("b", start="2", end="2"),
        start="2",
    )


def test_two_nodes_different_era_inside_affix():
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b")))

    assert build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", end="1"),
        LeafEvolveQuery("b", end="1"),
        start="1",
    )


def test_three_nodes_at_most_one_era():
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))
    c = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("c")))

    assert build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")),
        LeafEvolveQuery("c"),
    )

    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("c", Rule("1")))
    )

    assert build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"), end="1"
        ),
        LeafEvolveQuery("c", start="1", end="1"),
        start="1",
    )

    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("c", Rule("1")))
    )

    assert build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX,
            LeafEvolveQuery("a", end="1"),
            LeafEvolveQuery("b", start="1", end="1"),
            start="1",
            end="1",
        ),
        LeafEvolveQuery("c", start="1", end="1"),
        start="1",
    )

    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("c", Rule("1")))
    )

    assert build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX,
            LeafEvolveQuery("a", start="1", end="1"),
            LeafEvolveQuery("b", start="1", end="1"),
            start="1",
            end="1",
        ),
        LeafEvolveQuery("c", start="1", end="1"),
        start="1",
    )


def test_three_nodes_two_eras():
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("c", Rule("2")))
    )

    assert build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX,
            LeafEvolveQuery("a", end="1"),
            LeafEvolveQuery("b", start="1", end="1"),
            start="1",
            end="2",
        ),
        LeafEvolveQuery("c", start="2", end="2"),
        start="2",
    )

    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("c", Rule("2")))
    )

    assert build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX,
            LeafEvolveQuery("a", start="1", end="1"),
            LeafEvolveQuery("b", start="1", end="1"),
            start="1",
            end="2",
        ),
        LeafEvolveQuery("c", start="2", end="2"),
        start="2",
    )


def test_node_query():
    a_b = NodeEvolveQuery(AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"))

    assert a_b.get_query({}) == "ab"

    a_b = NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )

    assert a_b.get_query({}) == "ab"

    with pytest.raises(AssertionError):
        a_b = NodeEvolveQuery(
            AffixType.SUFFIX,
            LeafEvolveQuery("a", end="1"),
            LeafEvolveQuery("b", start="1", end="1"),
            start="1",
        )

        assert a_b.get_query({})


def test_single_layer():
    query = NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")),
        LeafEvolveQuery("c"),
    )

    assert query.get_query({}) == "abc"

    assert order_in_layers([query]) == [[query]]


def test_two_layers():
    query = NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"), end="1"
        ),
        LeafEvolveQuery("c", start="1", end="1"),
        start="1",
    )

    assert order_in_layers([query]) == [
        [
            NodeEvolveQuery(
                AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"), end="1"
            )
        ],
        [query],
    ]


def test_build_and_order():
    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("c", Rule("2")))
    )
    form = a.extend(b, c)

    assert build_and_order([form]) == (
        {
            form: NodeEvolveQuery(
                AffixType.SUFFIX,
                NodeEvolveQuery(
                    AffixType.SUFFIX,
                    LeafEvolveQuery("a", start="1", end="1"),
                    LeafEvolveQuery("b", start="1", end="1"),
                    start="1",
                    end="2",
                ),
                LeafEvolveQuery("c", start="2", end="2"),
                start="2",
            )
        },
        [
            [
                NodeEvolveQuery(
                    AffixType.SUFFIX,
                    LeafEvolveQuery("a", start="1", end="1"),
                    LeafEvolveQuery("b", start="1", end="1"),
                    start="1",
                    end="2",
                )
            ],
            [
                NodeEvolveQuery(
                    AffixType.SUFFIX,
                    NodeEvolveQuery(
                        AffixType.SUFFIX,
                        LeafEvolveQuery("a", start="1", end="1"),
                        LeafEvolveQuery("b", start="1", end="1"),
                        start="1",
                        end="2",
                    ),
                    LeafEvolveQuery("c", start="2", end="2"),
                    start="2",
                )
            ],
        ],
    )
