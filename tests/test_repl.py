from collections.abc import Generator
from inspect import cleandoc
from pathlib import Path

import pytest
from prompt_toolkit.input import PipeInput
from pytest import CaptureFixture

from pyconlang.metadata import Metadata
from pyconlang.repl import Mode, ReplSession, create_session
from pyconlang.repl import run as run_repl


@pytest.fixture
def simple_repl(simple_pyconlang: Path) -> Generator[ReplSession, None, None]:
    with create_session() as session:
        yield session


@pytest.fixture
def repl_with_archaic_default(
    simple_pyconlang: Path,
) -> Generator[ReplSession, None, None]:
    metadata = Metadata.default()
    metadata.scope = "archaic"
    metadata.save()

    with create_session() as session:
        yield session

    metadata.scope = "modern"
    metadata.save()


def test_basic(simple_repl: ReplSession) -> None:
    assert simple_repl.run_line("*apaki") == "abashi [abaʃi]"
    assert simple_repl.run_line("<big>") == "ishi [iʃi]"
    assert simple_repl.run_line("<big>", Mode.NORMAL) == "ishi [iʃi]"
    assert simple_repl.run_line("<big>.PL") == "ishiigi [iʃiigi]"
    assert simple_repl.run_line("*apak +! *i") == "abashi [abaʃi]"
    assert simple_repl.run_line("*apak +!@era1 *i") == "abagi [abagi]"
    assert simple_repl.run_line("<stone>") == "kaba [kaba]"
    assert simple_repl.run_line("% <stone>") == "apak [apak]"


def test_default_scope(repl_with_archaic_default: ReplSession) -> None:
    assert repl_with_archaic_default.run_line("<stone>") == "apak [apak]"
    assert repl_with_archaic_default.run_line("%modern <stone>") == "kaba [kaba]"
    assert (
        repl_with_archaic_default.run_line("STONE.<stone>") == "apakmaapak [apakmaapak]"
    )
    assert (
        repl_with_archaic_default.run_line("%modern STONE.<stone>")
        == "kabamagaba [kabamagaba]"
    )
    assert repl_with_archaic_default.run_line("<stone>", Mode.TRACE) == ""
    assert repl_with_archaic_default.run_line("%modern <stone>", Mode.TRACE) == (
        "kapa\nkapa => kaba (intervocalic-voicing)"
    )


def test_gloss(simple_repl: ReplSession) -> None:
    assert simple_repl.run_line("<big>.PL", Mode.GLOSS) == " ishiigi  \n <big>.PL "

    assert (
        simple_repl.run_line("<stone> <big>.PL", Mode.GLOSS)
        == "  kaba     ishiigi  \n <stone>   <big>.PL "
    )


def test_lookup(simple_repl: ReplSession) -> None:
    assert (
        simple_repl.run_line("<big>.PL", Mode.LOOKUP)
        == "<big>: (adj.) big, great\n.PL: plural for inanimate"
    )
    assert simple_repl.run_line("<big>.PL <stone>.PL", Mode.LOOKUP) == cleandoc(
        """
        Records for <big>.PL
        <big>: (adj.) big, great
        .PL: plural for inanimate
        
        Records for <stone>.PL
        <stone>: (n.) stone, pebble
        .PL: plural for inanimate
        """
    )


def test_trace(simple_repl: ReplSession) -> None:
    assert simple_repl.run_line("<big>", Mode.TRACE) == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃi => ishi (Romanizer)
        """
    )

    assert simple_repl.run_line("<big>.PL", Mode.TRACE) == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃiiki
        iʃiiki => iʃiigi (intervocalic-voicing)
        iʃiigi => ishiigi (Romanizer)
        """
    )

    assert simple_repl.run_line("<big> <stone>", Mode.TRACE) == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃi => ishi (Romanizer)
        kapa
        kapa => kaba (intervocalic-voicing)
        """
    )


def test_repl_interactive(
    capsys: CaptureFixture[str], mock_input: PipeInput, simple_pyconlang: Path
) -> None:
    mock_input.send_text("*apaki\n")
    mock_input.close()

    run_repl()

    captured = capsys.readouterr()

    assert captured.out == "abashi [abaʃi]\nGoodbye.\n"


def test_repl_command(capsys: CaptureFixture[str], simple_pyconlang: Path) -> None:
    run_repl("*apaki *baki")

    captured = capsys.readouterr()

    assert captured.out == "abashi [abaʃi] bashi [baʃi]\n"
