import os
import tempfile
from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from pyconlang.cli import init


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)


@pytest.fixture
def tmp_pyconlang(tmpdir):
    init.callback(tmpdir, "TestLang", "Mr. Tester", False)

    yield tmpdir


@pytest.fixture
def sample_lexicon():
    return """
    template &plural $ $.PL
    
    affix .PL *iki@era1 (<big> <pile>) plural for inanimate

    entry <strong> *kipu@era1 (adj.) strong, stable
    
    entry &plural <stone> *apak (n.) stone, pebble
    
    entry <gravel> <stone>.PL (n.) gravel
    """


@pytest.fixture
def simple_pyconlang(tmp_pyconlang, sample_lexicon):
    (tmp_pyconlang / "changes.lsc").write_text(
        """
    Class vowel {a, e, i, o, u}

    palatalization:
        k => ʃ / _ i
    
    era1:
        unchanged
    
    intervocalic-voicing:
        {p, t, k, s} => {b, d, g, z} / @vowel _ @vowel
    
    romanizer:
        ʃ => sh
    """
    )

    (tmp_pyconlang / "lexicon.txt").write_text(sample_lexicon)

    yield tmp_pyconlang


@pytest.fixture(autouse=True, scope="function")
def mock_input():
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input
