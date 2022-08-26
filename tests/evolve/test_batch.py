import pytest

from pyconlang.evolve.batch import Batcher, LeafEvolveQuery, NodeEvolveQuery
from pyconlang.evolve.errors import BadAffixation
from pyconlang.types import AffixType, Proto, ResolvedAffix, ResolvedForm, Rule


@pytest.fixture(scope="session")
def batcher():
    return Batcher()


def test_one_node(batcher):
    a = ResolvedForm(Proto("a"))
    assert batcher.build_query(a) == LeafEvolveQuery("a")

    a = ResolvedForm(Proto("a", Rule("1")))
    assert batcher.build_query(a) == LeafEvolveQuery("a", start="1")


def test_two_nodes_same(batcher):
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))

    assert batcher.build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")
    )

    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )

    assert batcher.build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )


def test_two_nodes_different(batcher):
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )

    assert batcher.build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )

    with pytest.raises(BadAffixation):
        a = ResolvedForm(Proto("a", Rule("1")))
        b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))

        batcher.build_query(a.extend(b))

    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("b", Rule("2")))
    )
    assert batcher.build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="2"),
        LeafEvolveQuery("b", start="2", end="2"),
        start="2",
    )


def test_two_nodes_different_era_inside_affix(batcher):
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b")))

    assert batcher.build_query(a.extend(b)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", end="1"),
        LeafEvolveQuery("b", end="1"),
        start="1",
    )


def test_three_nodes_at_most_one_era(batcher):
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))
    c = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("c")))

    assert batcher.build_query(a.extend(b, c)) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")),
        LeafEvolveQuery("c"),
    )

    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Proto("b")))
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("c", Rule("1")))
    )

    assert batcher.build_query(a.extend(b, c)) == NodeEvolveQuery(
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

    assert batcher.build_query(a.extend(b, c)) == NodeEvolveQuery(
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

    assert batcher.build_query(a.extend(b, c)) == NodeEvolveQuery(
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


def test_three_nodes_two_eras(batcher):
    a = ResolvedForm(Proto("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("c", Rule("2")))
    )

    assert batcher.build_query(a.extend(b, c)) == NodeEvolveQuery(
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

    assert batcher.build_query(a.extend(b, c)) == NodeEvolveQuery(
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


def test_node_query(batcher):
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


def test_single_layer(batcher):
    query = NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")),
        LeafEvolveQuery("c"),
    )

    assert query.get_query({}) == "abc"

    assert batcher.order_in_layers([query]) == [[query]]


def test_two_layers(batcher):
    query = NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"), end="1"
        ),
        LeafEvolveQuery("c", start="1", end="1"),
        start="1",
    )

    assert batcher.order_in_layers([query]) == [
        [
            NodeEvolveQuery(
                AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"), end="1"
            )
        ],
        [query],
    ]


def test_build_and_order(batcher):
    a = ResolvedForm(Proto("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Proto("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Proto("c", Rule("2")))
    )
    form = a.extend(b, c)

    assert batcher.build_and_order([form]) == (
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
