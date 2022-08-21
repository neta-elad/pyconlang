from pyconlang.evolve import Evolved, evolve, evolve_proto, evolve_word, glom_at
from pyconlang.types import Affix, AffixType, Proto, ResolvedAffix, ResolvedForm, Rule


def test_evolve(simple_pyconlang):
    assert evolve_word("apaki") == Evolved("apaki", "abashi", "abaʃi")
    assert evolve_word("apakí") == Evolved("apakí", "abashí", "abaʃí")
    assert evolve_proto(Proto("apaki", None)) == Evolved("apaki", "abashi", "abaʃi")

    assert evolve_word("apaki", end=Rule("era1")) == Evolved("apaki", "apaʃi", "apaʃi")

    assert evolve_word("apaki", start=Rule("era1")) == Evolved(
        "apaki", "abagi", "abagi"
    )
    assert evolve_proto(Proto("apaki", Rule("era1"))) == Evolved(
        "apaki", "abagi", "abagi"
    )

    assert glom_at("apak", "iki", Rule("era1")) == Evolved(
        "apakiʃi", "abagishi", "abagiʃi"
    )

    assert evolve(
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
    ) == Evolved("apakiʃi", "abagishi", "abagiʃi")


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
        ).modern
        == "maabak"
    )
