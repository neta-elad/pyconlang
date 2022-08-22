from pyconlang.evolve import Evolved, Evolver
from pyconlang.types import AffixType, Proto, ResolvedAffix, ResolvedForm, Rule


def test_evolve(simple_evolver):
    assert Evolver.evolve_words(["apaki", "apakí"]) == [
        Evolved("apaki", "abashi", "abaʃi"),
        Evolved("apakí", "abashí", "abaʃí"),
    ]

    assert Evolver.evolve_words(["apaki"], end="era1") == [
        Evolved("apaki", "apaʃi", "apaʃi")
    ]

    assert Evolver.evolve_words(["apaki"], start="era1") == [
        Evolved("apaki", "abagi", "abagi")
    ]

    assert simple_evolver.evolve_single(Proto("apaki")) == Evolved(
        "apaki", "abashi", "abaʃi"
    )

    assert simple_evolver.evolve_single(Proto("apaki", Rule("era1"))) == Evolved(
        "apaki", "abagi", "abagi"
    )

    assert simple_evolver.evolve_single(
        ResolvedForm(
            Proto("apak"),
            (
                ResolvedAffix(
                    False,
                    AffixType.SUFFIX,
                    Rule("era1"),
                    ResolvedForm(Proto("iki"), ()),
                ),
            ),
        )
    ) == Evolved("apakiʃi", "abagishi", "abagiʃi")


def test_proto_glom(simple_evolver):
    assert (
        simple_evolver.evolve_single(
            ResolvedForm(
                Proto("apak"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Proto("ma"), ()),
                    ),
                ),
            )
        ).modern
        == "maabak"
    )
