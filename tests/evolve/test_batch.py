import pytest

from pyconlang.domain import Component, Compound, Joiner, Morpheme, Rule
from pyconlang.evolve.arrange import AffixArranger
from pyconlang.evolve.batch import Batcher, ComponentQuery, CompoundQuery
from pyconlang.evolve.errors import BadAffixation


def test_one_node(batcher: Batcher, arranger: AffixArranger) -> None:
    a = Component(Morpheme("a"))
    assert batcher.build_query(arranger.rearrange(a)) == ComponentQuery("a")

    a = Component(Morpheme("a", Rule("1")))
    assert batcher.build_query(arranger.rearrange(a)) == ComponentQuery("a", start="1")


def test_two_nodes_same(batcher: Batcher, arranger: AffixArranger) -> None:
    a = Component(Morpheme("a"))
    b = Component(Morpheme("b"))

    form = arranger.rearrange(Compound(a, Joiner.head(), b))

    assert batcher.build_query(form) == CompoundQuery(
        ComponentQuery("a"), Joiner.head(), ComponentQuery("b")
    )

    a = Component(Morpheme("a", Rule("1")))
    b = Component(Morpheme("b", Rule("1")))

    form = arranger.rearrange(Compound(a, Joiner.head(Rule("1")), b))

    assert batcher.build_query(form) == CompoundQuery(
        ComponentQuery("a", start="1", end="1"),
        Joiner.head(Rule("1")),
        ComponentQuery("b", start="1", end="1"),
    )


def test_two_nodes_different(batcher: Batcher, arranger: AffixArranger) -> None:
    a = Component(Morpheme("a"))
    b = Component(Morpheme("b", Rule("1")))

    form = arranger.rearrange(Compound(a, Joiner.head(Rule("1")), b))

    assert batcher.build_query(form) == CompoundQuery(
        ComponentQuery("a", end="1"),
        Joiner.head(Rule("1")),
        ComponentQuery("b", start="1", end="1"),
    )

    with pytest.raises(BadAffixation):
        a = Component(Morpheme("a", Rule("1")))
        b = Component(Morpheme("b"))
        form = Compound(a, Joiner.head(), b)
        batcher.build_query(form)

    a = Component(Morpheme("a", Rule("1")))
    b = Component(Morpheme("b", Rule("2")))

    form = arranger.rearrange(Compound(a, Joiner.head(Rule("2")), b))

    assert batcher.build_query(form) == CompoundQuery(
        ComponentQuery("a", start="1", end="2"),
        Joiner.head(Rule("2")),
        ComponentQuery("b", start="2", end="2"),
    )


def test_two_nodes_different_era_inside_affix(
    batcher: Batcher, arranger: AffixArranger
) -> None:
    a = Component(Morpheme("a"))
    b = Component(Morpheme("b"))

    form = arranger.rearrange(Compound(a, Joiner.head(Rule("1")), b))

    assert batcher.build_query(form) == CompoundQuery(
        ComponentQuery("a", end="1"),
        Joiner.head(Rule("1")),
        ComponentQuery("b", end="1"),
    )


def test_three_nodes_at_most_one_era(batcher: Batcher, arranger: AffixArranger) -> None:
    a = Component(Morpheme("a"))
    b = Component(Morpheme("b"))
    c = Component(Morpheme("c"))

    form = arranger.rearrange(Compound(Compound(a, Joiner.head(), b), Joiner.head(), c))

    assert batcher.build_query(form) == CompoundQuery(
        CompoundQuery(ComponentQuery("a"), Joiner.head(), ComponentQuery("b")),
        Joiner.head(),
        ComponentQuery("c"),
    )

    a = Component(Morpheme("a"))
    b = Component(Morpheme("b"))
    c = Component(Morpheme("c", Rule("1")))

    form = arranger.rearrange(
        Compound(a, Joiner.head(), Compound(b, Joiner.head(Rule("1")), c))
    )

    assert batcher.build_query(form) == CompoundQuery(
        CompoundQuery(ComponentQuery("a"), Joiner.head(), ComponentQuery("b"), end="1"),
        Joiner.head(Rule("1")),
        ComponentQuery("c", start="1", end="1"),
    )

    a = Component(Morpheme("a"))
    b = Component(Morpheme("b", Rule("1")))
    c = Component(Morpheme("c", Rule("1")))

    form = arranger.rearrange(
        Compound(Compound(a, Joiner.head(Rule("1")), b), Joiner.head(Rule("1")), c)
    )

    assert batcher.build_query(form) == CompoundQuery(
        CompoundQuery(
            ComponentQuery("a", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("b", start="1", end="1"),
            end="1",
        ),
        Joiner.head(Rule("1")),
        ComponentQuery("c", start="1", end="1"),
    )

    a = Component(Morpheme("a", Rule("1")))
    b = Component(Morpheme("b", Rule("1")))
    c = Component(Morpheme("c", Rule("1")))

    form = arranger.rearrange(
        Compound(a, Joiner.head(Rule("1")), Compound(b, Joiner.head(Rule("1")), c))
    )
    assert batcher.build_query(form) == CompoundQuery(
        ComponentQuery("a", start="1", end="1"),
        Joiner.head(Rule("1")),
        CompoundQuery(
            ComponentQuery("b", start="1", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("c", start="1", end="1"),
            end="1",
        ),
    )


def test_three_nodes_two_eras(batcher: Batcher, arranger: AffixArranger) -> None:
    a = Component(Morpheme("a"))
    b = Component(Morpheme("b", Rule("1")))
    c = Component(Morpheme("c", Rule("2")))

    assert batcher.build_query(
        arranger.rearrange(
            Compound(a, Joiner.head(Rule("1")), Compound(b, Joiner.head(Rule("2")), c))
        )
    ) == CompoundQuery(
        CompoundQuery(
            ComponentQuery("a", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("b", start="1", end="1"),
            end="2",
        ),
        Joiner.head(Rule("2")),
        ComponentQuery("c", start="2", end="2"),
    )

    a = Component(Morpheme("a", Rule("1")))
    b = Component(Morpheme("b", Rule("1")))
    c = Component(Morpheme("c", Rule("2")))

    assert batcher.build_query(
        arranger.rearrange(
            Compound(a, Joiner.head(Rule("1")), Compound(b, Joiner.head(Rule("2")), c))
        )
    ) == CompoundQuery(
        CompoundQuery(
            ComponentQuery("a", start="1", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("b", start="1", end="1"),
            end="2",
        ),
        Joiner.head(Rule("2")),
        ComponentQuery("c", start="2", end="2"),
    )


def test_node_query(batcher: Batcher) -> None:
    a_b = CompoundQuery(ComponentQuery("a"), Joiner.head(), ComponentQuery("b"))

    assert a_b.get_query({}) == "ab"

    a_b = CompoundQuery(
        ComponentQuery("a", start="1", end="1"),
        Joiner.head(Rule("1")),
        ComponentQuery("b", start="1", end="1"),
    )

    assert a_b.get_query({}) == "ab"

    with pytest.raises(AssertionError):
        a_b = CompoundQuery(
            ComponentQuery("a", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("b", start="1", end="1"),
        )

        assert a_b.get_query({})


def test_single_layer(batcher: Batcher) -> None:
    query = CompoundQuery(
        CompoundQuery(ComponentQuery("a"), Joiner.head(), ComponentQuery("b")),
        Joiner.head(),
        ComponentQuery("c"),
    )

    assert query.get_query({}) == "abc"

    assert batcher.order_in_layers([query]) == [[query]]


def test_two_layers(batcher: Batcher) -> None:
    query = CompoundQuery(
        CompoundQuery(ComponentQuery("a"), Joiner.head(), ComponentQuery("b"), end="1"),
        Joiner.head(Rule("2")),
        ComponentQuery("c", start="1", end="1"),
    )

    assert batcher.order_in_layers([query]) == [
        [
            CompoundQuery(
                ComponentQuery("a"), Joiner.head(), ComponentQuery("b"), end="1"
            )
        ],
        [query],
    ]


def test_build_and_order(batcher: Batcher, arranger: AffixArranger) -> None:
    a = Component(Morpheme("a", Rule("1")))
    b = Component(Morpheme("b", Rule("1")))
    c = Component(Morpheme("c", Rule("2")))

    form = arranger.rearrange(
        Compound(a, Joiner.head(Rule("1")), Compound(b, Joiner.head(Rule("2")), c))
    )

    mapping, layered_queries = batcher.build_and_order([form])

    assert len(mapping) == 1
    assert form in mapping
    assert mapping[form] == CompoundQuery(
        CompoundQuery(
            ComponentQuery("a", start="1", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("b", start="1", end="1"),
            end="2",
        ),
        Joiner.head(Rule("2")),
        ComponentQuery("c", start="2", end="2"),
    )
    assert len(layered_queries) == 2
    assert len(layered_queries[0]) == 1
    assert layered_queries[0][0] == CompoundQuery(
        ComponentQuery("a", start="1", end="1"),
        Joiner.head(Rule("1")),
        ComponentQuery("b", start="1", end="1"),
        end="2",
    )
    assert len(layered_queries[1]) == 1
    assert layered_queries[1][0] == CompoundQuery(
        CompoundQuery(
            ComponentQuery("a", start="1", end="1"),
            Joiner.head(Rule("1")),
            ComponentQuery("b", start="1", end="1"),
            end="2",
        ),
        Joiner.head(Rule("2")),
        ComponentQuery("c", start="2", end="2"),
    )
