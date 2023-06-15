import pytest

from pyconlang.evolve.arrange import AffixArranger
from pyconlang.evolve.batch import Batcher, LeafEvolveQuery, NodeEvolveQuery
from pyconlang.evolve.errors import BadAffixation
from pyconlang.types import AffixType, Morpheme, ResolvedAffix, ResolvedForm, Rule


@pytest.fixture(scope="session")
def batcher():
    return Batcher()


@pytest.fixture(scope="session")
def arranger():
    return AffixArranger(["1", "2"])


def test_one_node(batcher, arranger):
    a = ResolvedForm(Morpheme("a"))
    assert batcher.build_query(arranger.rearrange(a)) == LeafEvolveQuery("a")

    a = ResolvedForm(Morpheme("a", Rule("1")))
    assert batcher.build_query(arranger.rearrange(a)) == LeafEvolveQuery("a", start="1")


def test_two_nodes_same(batcher, arranger):
    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Morpheme("b")))

    assert batcher.build_query(arranger.rearrange(a.extend_any(b))) == NodeEvolveQuery(
        AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")
    )

    a = ResolvedForm(Morpheme("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )

    assert batcher.build_query(arranger.rearrange(a.extend_any(b))) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )


def test_two_nodes_different(batcher, arranger):
    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )

    assert batcher.build_query(arranger.rearrange(a.extend_any(b))) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", end="1"),
        LeafEvolveQuery("b", start="1", end="1"),
        start="1",
    )

    with pytest.raises(BadAffixation):
        a = ResolvedForm(Morpheme("a", Rule("1")))
        b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Morpheme("b")))

        batcher.build_query(arranger.rearrange(a.extend_any(b)))

    a = ResolvedForm(Morpheme("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Morpheme("b", Rule("2")))
    )
    assert batcher.build_query(arranger.rearrange(a.extend_any(b))) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", start="1", end="2"),
        LeafEvolveQuery("b", start="2", end="2"),
        start="2",
    )


def test_two_nodes_different_era_inside_affix(batcher, arranger):
    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b")))

    assert batcher.build_query(arranger.rearrange(a.extend_any(b))) == NodeEvolveQuery(
        AffixType.SUFFIX,
        LeafEvolveQuery("a", end="1"),
        LeafEvolveQuery("b", end="1"),
        start="1",
    )


def test_three_nodes_at_most_one_era(batcher, arranger):
    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Morpheme("b")))
    c = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Morpheme("c")))

    assert batcher.build_query(
        arranger.rearrange(a.extend_any(b).extend_any(c))
    ) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b")),
        LeafEvolveQuery("c"),
    )

    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(False, AffixType.SUFFIX, None, ResolvedForm(Morpheme("b")))
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("c", Rule("1")))
    )

    assert batcher.build_query(
        arranger.rearrange(a.extend_any(b).extend_any(c))
    ) == NodeEvolveQuery(
        AffixType.SUFFIX,
        NodeEvolveQuery(
            AffixType.SUFFIX, LeafEvolveQuery("a"), LeafEvolveQuery("b"), end="1"
        ),
        LeafEvolveQuery("c", start="1", end="1"),
        start="1",
    )

    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("c", Rule("1")))
    )

    assert batcher.build_query(
        arranger.rearrange(a.extend_any(b).extend_any(c))
    ) == NodeEvolveQuery(
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

    a = ResolvedForm(Morpheme("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("c", Rule("1")))
    )

    assert batcher.build_query(
        arranger.rearrange(a.extend_any(b).extend_any(c))
    ) == NodeEvolveQuery(
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


def test_three_nodes_two_eras(batcher, arranger):
    a = ResolvedForm(Morpheme("a"))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Morpheme("c", Rule("2")))
    )

    assert batcher.build_query(
        arranger.rearrange(a.extend_any(b).extend_any(c))
    ) == NodeEvolveQuery(
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

    a = ResolvedForm(Morpheme("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Morpheme("c", Rule("2")))
    )

    assert batcher.build_query(
        arranger.rearrange(a.extend_any(b).extend_any(c))
    ) == NodeEvolveQuery(
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


def test_build_and_order(batcher, arranger):
    a = ResolvedForm(Morpheme("a", Rule("1")))
    b = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("1"), ResolvedForm(Morpheme("b", Rule("1")))
    )
    c = ResolvedAffix(
        False, AffixType.SUFFIX, Rule("2"), ResolvedForm(Morpheme("c", Rule("2")))
    )
    form = arranger.rearrange(a.extend_any(b).extend_any(c))

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
