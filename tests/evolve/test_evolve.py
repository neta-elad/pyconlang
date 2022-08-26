from pyconlang.evolve import Evolved, TraceLine
from pyconlang.types import AffixType, Proto, ResolvedAffix, ResolvedForm, Rule


def test_evolve_words(simple_evolver):
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


def test_evolve_forms(simple_evolver):
    assert simple_evolver.evolve([Proto("apaki")]) == [
        Evolved("apaki", "abashi", "abaʃi")
    ]

    assert simple_evolver.evolve([Proto("apaki", Rule("era1"))]) == [
        Evolved("apaki", "abagi", "abagi")
    ]

    assert simple_evolver.evolve(
        [
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
        ]
    ) == [Evolved("apakiʃi", "abagishi", "abagiʃi")]


def test_proto_glom(simple_evolver):
    assert simple_evolver.evolve(
        [
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
        ]
    ) == [Evolved("maapak", "maabak", "maabak")]


def test_stress(simple_evolver):
    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Proto("apˈak"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Proto("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("maapˈak", "maabik", "maabˈik")]

    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Proto("apˈak"),
                (
                    ResolvedAffix(
                        True,
                        AffixType.PREFIX,
                        None,
                        ResolvedForm(Proto("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("mˈaapak", "miabak", "mˈiabak")]

    assert simple_evolver.evolve(
        [
            ResolvedForm(
                Proto("apˈak"),
                (
                    ResolvedAffix(
                        True,
                        AffixType.PREFIX,
                        Rule("era2"),
                        ResolvedForm(Proto("mˈa"), ()),
                    ),
                ),
            )
        ]
    ) == [Evolved("mˈiabik", "miabik", "mˈiabik")]


def test_trace(simple_evolver):
    assert simple_evolver.trace([Proto("apaki")]) == [
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
                Proto("apaki"),
                (
                    ResolvedAffix(
                        False,
                        AffixType.PREFIX,
                        Rule("era1"),
                        ResolvedForm(Proto("ma"), ()),
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
