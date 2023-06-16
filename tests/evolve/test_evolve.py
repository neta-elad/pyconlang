from pyconlang.domain import AffixType, Morpheme, ResolvedAffix, ResolvedForm, Rule
from pyconlang.evolve import Evolver
from pyconlang.evolve.domain import Evolved
from pyconlang.evolve.tracer import TraceLine
from pyconlang.metadata import Metadata


def test_evolve_words(simple_evolver: Evolver) -> None:
    assert simple_evolver.evolve_words(["apaki", "apakí"]) == (
        [
            Evolved("apaki", "abashi", "abaʃi"),
            Evolved("apakí", "abashí", "abaʃí"),
        ],
        {},
    )

    assert simple_evolver.evolve_words(["apaki"], end="era1") == (
        [Evolved("apaki", "apaʃi", "apaʃi")],
        {},
    )

    assert simple_evolver.evolve_words(["apaki"], start="era1") == (
        [Evolved("apaki", "abagi", "abagi")],
        {},
    )


def test_evolve_forms(simple_evolver: Evolver) -> None:
    assert simple_evolver.evolve([Morpheme("apaki")]) == [
        Evolved("apaki", "abashi", "abaʃi")
    ]

    assert simple_evolver.evolve([Morpheme("apaki", Rule("era1"))]) == [
        Evolved("apaki", "abagi", "abagi")
    ]

    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("apak"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.SUFFIX,
                        Rule("era1"),
                        ResolvedForm(Morpheme("iki"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("apakiʃi", "abagishi", "abagiʃi")]


def test_morpheme_fuse(simple_evolver: Evolver) -> None:
    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("apak"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Morpheme("ma"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("maapak", "maabak", "maabak")]


def test_morpheme_fuse_order(simple_evolver: Evolver) -> None:
    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("paka"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Morpheme("ma"), ()),
                    ),
                ),
                (
                    ResolvedAffix(
                        False,
                        AffixType.SUFFIX,
                        Rule("era2"),
                        ResolvedForm(Morpheme("ka"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("mabagaka", "mabagaka", "mabagaka")]


def test_stress(simple_evolver: Evolver) -> None:
    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("apˈak"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Morpheme("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("maapˈak", "maabik", "maabˈik")]

    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("apˈak"),
                (
                    ResolvedAffix(
                        True,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Morpheme("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("mˈaapak", "miabak", "mˈiabak")]

    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("apˈak"),
                (
                    ResolvedAffix(
                        True,
                        AffixType.PREFIX,
                        Rule("era2"),
                        ResolvedForm(Morpheme("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("mˈiabik", "miabik", "mˈiabik")]


def test_explicit_syllables(simple_evolver: Evolver) -> None:
    Metadata.default().syllables = True
    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("apˈak"),
                (
                    ResolvedAffix(
                        True,
                        AffixType.PREFIX,
                        Rule("era2"),
                        ResolvedForm(Morpheme("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("mˈi.abik", "miabik", "mˈi.abik")]
    Metadata.default().syllables = False


def test_evolve_empty_stem(simple_evolver: Evolver) -> None:
    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Morpheme("", Rule("era2")),
                (
                    ResolvedAffix(
                        True,
                        AffixType.PREFIX,
                        Rule("era2"),
                        ResolvedForm(Morpheme("apak"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("abak", "abak", "abak")]


def test_trace(simple_evolver: Evolver) -> None:
    assert simple_evolver.trace([Morpheme("apaki")]) == [
        (
            Evolved("apaki", "abashi", "abaʃi"),
            [
                (
                    "apaki",
                    [
                        TraceLine("palatalization", "apaki", "apaki", "apaʃi"),
                        TraceLine("intervocalic-voicing", "apaki", "apaʃi", "abaʃi"),
                        TraceLine("Romanizer", "apaki", "abaʃi", "abashi"),
                    ],
                )
            ],
        )
    ]

    assert simple_evolver.trace(
        [
            ResolvedForm(
                Morpheme("apaki"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        Rule("era1"),
                        ResolvedForm(Morpheme("ma"), ()),
                    ),
                ),
            )
        ]
    ) == [
        (
            Evolved("maapaʃi", "maabashi", "maabaʃi"),
            [
                ("apaki", [TraceLine("palatalization", "apaki", "apaki", "apaʃi")]),
                (
                    "maapaʃi",
                    [
                        TraceLine(
                            "intervocalic-voicing", "maapaʃi", "maapaʃi", "maabaʃi"
                        ),
                        TraceLine("Romanizer", "maapaʃi", "maabaʃi", "maabashi"),
                    ],
                ),
            ],
        )
    ]
