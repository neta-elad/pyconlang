from pathlib import Path

from pyconlang.domain import Component, Compound, Joiner, Morpheme, Rule
from pyconlang.evolve import Evolver
from pyconlang.evolve.domain import Evolved
from pyconlang.lexurgy.domain import TraceLine
from pyconlang.metadata import Metadata


def test_evolve_words(
    simple_evolver: Evolver, modern_changes_path: Path, ultra_modern_changes_path: Path
) -> None:
    assert simple_evolver.evolve_words(
        ["apaki", "apakí"], changes=modern_changes_path
    ) == (
        [
            Evolved("apaki", "abashi", "abaʃi"),
            Evolved("apakí", "abashí", "abaʃí"),
        ],
        {},
    )

    assert simple_evolver.evolve_words(
        ["apaki", "apakí"], changes=ultra_modern_changes_path
    ) == (
        [
            Evolved("apaki", "ibishi", "ibiʃi"),
            Evolved("apakí", "ibishí", "ibiʃí"),
        ],
        {},
    )

    assert simple_evolver.evolve_words(
        ["apaki"], end="era1", changes=modern_changes_path
    ) == (
        [Evolved("apaki", "apaʃi", "apaʃi")],
        {},
    )

    assert simple_evolver.evolve_words(
        ["apaki"], start="era1", changes=modern_changes_path
    ) == (
        [Evolved("apaki", "abagi", "abagi")],
        {},
    )


def test_evolve_forms(simple_evolver: Evolver, modern_changes_path: Path) -> None:
    assert simple_evolver.evolve(
        [Component(Morpheme("apaki"))], changes=modern_changes_path
    ) == [Evolved("apaki", "abashi", "abaʃi")]

    assert simple_evolver.evolve(
        [Component(Morpheme("apaki", Rule("era1")))], changes=modern_changes_path
    ) == [Evolved("apaki", "abagi", "abagi")]

    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("apak")),
                Joiner.head(Rule("era1")),
                Component(Morpheme("iki")),
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("apakiʃi", "abagishi", "abagiʃi")]


def test_morpheme_fuse(simple_evolver: Evolver, modern_changes_path: Path) -> None:
    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("ma")), Joiner.tail(), Component(Morpheme("apak"))
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("maapak", "maabak", "maabak")]


def test_morpheme_fuse_order(
    simple_evolver: Evolver, modern_changes_path: Path
) -> None:
    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("ma")),
                Joiner.tail(),
                Compound(
                    Component(Morpheme("paka")),
                    Joiner.head(Rule("era2")),
                    Component(Morpheme("ka")),
                ),
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("mabagaka", "mabagaka", "mabagaka")]


def test_stress(simple_evolver: Evolver, modern_changes_path: Path) -> None:
    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("mˈa")), Joiner.tail(), Component(Morpheme("apˈak"))
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("maapˈak", "maabik", "maabˈik")]

    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("mˈa")), Joiner.head(), Component(Morpheme("apˈak"))
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("mˈaapak", "miabak", "mˈiabak")]

    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("mˈa")),
                Joiner.head(Rule("era2")),
                Component(Morpheme("apˈak")),
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("mˈiabik", "miabik", "mˈiabik")]


def test_explicit_syllables(simple_evolver: Evolver, modern_changes_path: Path) -> None:
    Metadata.default().syllables = True
    assert simple_evolver.evolve(
        [
            Compound(
                Component(Morpheme("mˈa")),
                Joiner.head(Rule("era2")),
                Component(Morpheme("apˈak")),
            )
        ],
        changes=modern_changes_path,
    ) == [Evolved("mˈi.abik", "miabik", "mˈi.abik")]
    Metadata.default().syllables = False


def test_trace(simple_evolver: Evolver, modern_changes_path: Path) -> None:
    assert simple_evolver.trace(
        [Component(Morpheme("apaki"))], changes=modern_changes_path
    ) == [
        (
            Evolved("apaki", "abashi", "abaʃi"),
            [
                (
                    "apaki",
                    [
                        TraceLine("palatalization", "apaki", "apaki", "apaʃi"),
                        TraceLine("intervocalic-voicing", "apaki", "apaʃi", "abaʃi"),
                        TraceLine("modern", "apaki", "abaʃi", "abashi"),
                    ],
                )
            ],
        )
    ]

    assert simple_evolver.trace(
        [
            Compound(
                Component(Morpheme("ma")),
                Joiner.tail(Rule("era1")),
                Component(Morpheme("apaki")),
            )
        ],
        changes=modern_changes_path,
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
                        TraceLine("modern", "maapaʃi", "maabaʃi", "maabashi"),
                    ],
                ),
            ],
        )
    ]
