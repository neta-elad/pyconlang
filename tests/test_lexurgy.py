from pyconlang.lexurgy import evolve, evolve_proto, evolve_word, glom_at
from pyconlang.types import Affix, AffixType, Proto, ResolvedAffix, ResolvedForm, Rule


def test_evolve(simple_pyconlang):
    assert evolve_word("apaki") == "abashi"
    assert evolve_proto(Proto("apaki", None)) == "abashi"

    assert evolve_word("apaki", end=Rule("era1")) == "apaʃi"

    assert evolve_word("apaki", start=Rule("era1")) == "abagi"
    assert evolve_proto(Proto("apaki", Rule("era1"))) == "abagi"

    assert glom_at("apak", "iki", Rule("era1")) == "abagishi"

    assert (
        evolve(
            ResolvedForm(
                Proto("apak", None),
                (
                    ResolvedAffix(
                        False,
                        Affix("PL", AffixType.SUFFIX),
                        Rule("era1"),
                        ResolvedForm(Proto("iki", None), ()),
                    ),
                ),
            )
        )
        == "abagishi"
    )


def test_proto_glom(simple_pyconlang):
    assert (
        evolve(
            ResolvedForm(
                Proto("apak", None),
                (
                    ResolvedAffix(
                        False,
                        Affix("PL", AffixType.PREFIX),
                        None,
                        ResolvedForm(Proto("ma", None), ()),
                    ),
                ),
            )
        )
        == "maabak"
    )
