from inspect import cleandoc

import pytest

from pyconlang.cli import run_repl
from pyconlang.repl import ReplSession


@pytest.fixture
def simple_repl(capsys, simple_pyconlang):
    session = ReplSession()

    def evaluate(line: str) -> str:
        session.onecmd(line)
        return capsys.readouterr().out.strip()

    yield evaluate


def test_basic(simple_repl):
    assert simple_repl("*apaki") == "abashi"
    assert simple_repl("<big>") == "ishi"
    assert simple_repl("<big>.PL") == "ishiigi"


def test_phonetic(simple_repl):
    assert simple_repl("p *apaki") == "abaʃi"
    assert simple_repl("phonetic *apaki") == "abaʃi"
    assert simple_repl("phonetic <big>.PL") == "iʃiigi"


def test_simple(simple_repl):
    assert simple_repl("*apakí") == "abashí"
    assert simple_repl("s *apakí") == "abashi"
    assert simple_repl("simple *apakí") == "abashi"


def test_gloss(simple_repl):
    assert simple_repl("g <big>.PL") == "ishiigi  \n <big>.PL"
    assert simple_repl("gloss <big>.PL") == "ishiigi  \n <big>.PL"

    assert (
        simple_repl("gloss <stone> <big>.PL")
        == "abak     ishiigi  \n <stone>   <big>.PL"
    )


def test_lookup(simple_repl):
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


def test_trace(simple_repl):
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


def test_repl(capsys, mock_input, simple_pyconlang):
    mock_input.send_text("*apaki\n")
    mock_input.close()

    run_repl()

    captured = capsys.readouterr()

    assert captured.out == "abashi\nGoodbye.\n"

    run_repl("p *apaki *baki")

    captured = capsys.readouterr()

    assert captured.out == "abaʃi baʃi\n"
