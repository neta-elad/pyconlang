from collections.abc import Generator
from inspect import cleandoc
from pathlib import Path
from typing import Protocol

import pytest
from prompt_toolkit.input import PipeInput
from pytest import CaptureFixture

from pyconlang.metadata import Metadata
from pyconlang.repl import create_session
from pyconlang.repl import run as run_repl


class Evaluator(Protocol):
    def __call__(self, line: str) -> str:
        ...


@pytest.fixture
def simple_repl(
    capsys: CaptureFixture[str], simple_pyconlang: Path
) -> Generator[Evaluator, None, None]:
    with create_session() as session:

        def evaluate(line: str) -> str:
            session.onecmd(line)
            return capsys.readouterr().out.strip()

        yield evaluate


@pytest.fixture
def repl_with_modern_default(
    capsys: CaptureFixture[str], simple_pyconlang: Path
) -> Generator[Evaluator, None, None]:
    metadata = Metadata.default()
    metadata.lang = "modern"
    metadata.save()
    with create_session() as session:

        def evaluate(line: str) -> str:
            session.onecmd(line)
            return capsys.readouterr().out.strip()

        yield evaluate
    metadata.lang = None
    metadata.save()


def test_basic(simple_repl: Evaluator) -> None:
    assert simple_repl("*apaki") == "abashi"
    assert simple_repl("<big>") == "ishi"
    assert simple_repl("d <big>") == "ishi"
    assert simple_repl("d") == "ishi"
    assert simple_repl("<big>.PL") == "ishiigi"
    assert simple_repl("*apak +! *i") == "abashi"
    assert simple_repl("*apak +!@era1 *i") == "abagi"


def test_default_lang(repl_with_modern_default: Evaluator) -> None:
    assert repl_with_modern_default("p <stone>") == "kaba"
    assert repl_with_modern_default("p % <stone>") == "abak"
    assert repl_with_modern_default("p % STONE.<stone>") == "abakmaabak"
    assert repl_with_modern_default("p STONE.<stone>") == "abakmagaba"


def test_phonetic(simple_repl: Evaluator) -> None:
    assert simple_repl("p *apaki") == "abaʃi"
    assert simple_repl("*apaki") == "abashi"
    assert simple_repl("p") == "abaʃi"
    assert simple_repl("phonetic *apaki") == "abaʃi"
    assert simple_repl("phonetic <big>.PL") == "iʃiigi"
    assert simple_repl("p <stone>") == "abak"
    assert simple_repl("p %modern <stone>") == "kaba"


def test_simple(simple_repl: Evaluator) -> None:
    assert simple_repl("*apakí") == "abashí"
    assert simple_repl("s") == "abashi"
    assert simple_repl("s *apakí") == "abashi"
    assert simple_repl("simple *apakí") == "abashi"


def test_gloss(simple_repl: Evaluator) -> None:
    assert simple_repl("<big>.PL") == "ishiigi"
    assert simple_repl("g") == "ishiigi  \n <big>.PL"
    assert simple_repl("g <big>.PL") == "ishiigi  \n <big>.PL"
    assert simple_repl("gloss <big>.PL") == "ishiigi  \n <big>.PL"

    assert (
        simple_repl("gloss <stone> <big>.PL")
        == "abak     ishiigi  \n <stone>   <big>.PL"
    )


def test_lookup(simple_repl: Evaluator) -> None:
    assert simple_repl("<big>.PL") == "ishiigi"
    assert simple_repl("l") == "<big>: (adj.) big, great\n.PL: plural for inanimate"
    assert (
        simple_repl("l <big>.PL")
        == "<big>: (adj.) big, great\n.PL: plural for inanimate"
    )
    assert (
        simple_repl("lookup <big>.PL")
        == "<big>: (adj.) big, great\n.PL: plural for inanimate"
    )
    assert simple_repl("lookup <big>.PL <stone>.PL") == cleandoc(
        """
        Records for <big>.PL
        <big>: (adj.) big, great
        .PL: plural for inanimate
        
        Records for <stone>.PL
        <stone>: (n.) stone, pebble
        .PL: plural for inanimate
        """
    )


def test_trace(simple_repl: Evaluator) -> None:
    assert simple_repl("<big>") == "ishi"
    assert simple_repl("t") == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃi => ishi (Romanizer)
        """
    )
    assert simple_repl("t <big>") == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃi => ishi (Romanizer)
        """
    )
    assert simple_repl("trace <big>") == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃi => ishi (Romanizer)
        """
    )

    assert simple_repl("trace <big>.PL") == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃiiki
        iʃiiki => iʃiigi (intervocalic-voicing)
        iʃiigi => ishiigi (Romanizer)
        """
    )

    assert simple_repl("trace <big> <stone>") == cleandoc(
        """
        iki
        iki => iʃi (palatalization)
        iʃi => ishi (Romanizer)
        apak
        apak => abak (intervocalic-voicing)
        """
    )


def test_repl_interactive(
    capsys: CaptureFixture[str], mock_input: PipeInput, simple_pyconlang: Path
) -> None:
    mock_input.send_text("*apaki\n")
    mock_input.close()

    run_repl()

    captured = capsys.readouterr()

    assert captured.out == "abashi\nGoodbye.\n"


def test_repl_command(capsys: CaptureFixture[str], simple_pyconlang: Path) -> None:
    run_repl("p *apaki *baki")

    captured = capsys.readouterr()

    assert captured.out == "abaʃi baʃi\n"
