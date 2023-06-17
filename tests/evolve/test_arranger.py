from pyconlang.domain import Component, Compound, Joiner, Morpheme, Rule
from pyconlang.evolve.arrange import AffixArranger


def test_rearrange(arranger: AffixArranger) -> None:
    a = Component(Morpheme("a", Rule("1")))
    b = Component(Morpheme("b", Rule("1")))
    c = Component(Morpheme("c", Rule("2")))

    form = arranger.rearrange(
        Compound(a, Joiner.head(Rule("1")), Compound(b, Joiner.head(Rule("2")), c))
    )

    assert form == Compound(
        Compound(a, Joiner.head(Rule("1")), b), Joiner.head(Rule("2")), c
    )


def test_rearrange_with_empty_era(arranger: AffixArranger) -> None:
    a = Component(Morpheme("a"))
    b = Component(Morpheme("b"))
    c = Component(Morpheme("c", Rule("1")))

    form = arranger.rearrange(
        Compound(a, Joiner.head(), Compound(b, Joiner.head(Rule("1")), c))
    )

    assert form == Compound(Compound(a, Joiner.head(), b), Joiner.head(Rule("1")), c)
