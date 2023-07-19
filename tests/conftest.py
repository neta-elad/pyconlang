import os
import tempfile
from collections.abc import Generator
from inspect import cleandoc
from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output import DummyOutput

from pyconlang.cli import init


@pytest.fixture
def tmpdir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)


@pytest.fixture
def tmp_pyconlang(tmpdir: Path) -> Generator[Path, None, None]:
    assert init.callback is not None
    init.callback(tmpdir, "TestLang", "Mr. Tester", False, False)

    yield tmpdir


@pytest.fixture
def sample_lexicon() -> str:
    return cleandoc(
        """
        template &plural $ $.PL # this is a template
        
        affix .PL *iki@era1 (<big> <pile>) 
            plural for inanimate
        affix % .COL *ma collective
        
        affix .LARGE $.COL.PL large plural
        affix % STONE. <stone>.COL made of stone
        
        entry <pile> *ma (n.) pile
        
        affix .DIST-PL (<big> <pile>) distributive plural 
        
        entry <big> *iki (adj.) big, great
    
        entry 
            <strong> 
            *kipu@era1 
            (adj.) 
            strong, stable
        
        # here is how to use a template
        entry &plural % <stone> *apak (n.) stone, pebble
        
        entry %modern <stone> *kapa (n.) stone, pebble (modern)
        
        entry <gravel> <stone>.PL (n.) gravel
        
        lang %ultra-modern : %modern './ultra-modern.lsc'
        
        entry %ultra-modern <gravel> <stone>.DIST-PL (n.) gravel (ultra-modern)
        
        entry <gravel>.PL *ka (n.) gravel (plural)
        """
    )


@pytest.fixture
def sample_changes() -> str:
    return cleandoc(
        """
        Feature type (*consonant, vowel)
        Feature height (*low, mid, high)

        Feature +stressed

        Diacritic ˈ (before) [+stressed] (floating)

        Symbol a [low vowel]
        Symbol u [mid vowel]
        Symbol i [high vowel]

        syllables:
            explicit
    
        palatalization:
            k => ʃ / _ i
    
        era1:
            unchanged
    
        intervocalic-voicing:
            {p, t, k, s} => {b, d, g, z} / [vowel] _ [vowel]
    
        vowel-raising:
            [+stressed vowel] => [high]
    
        era2:
            unchanged
    
        romanizer-phonetic:
            unchanged
    
        syllables:
            clear
    
        romanizer:
            [+stressed vowel] => [*stressed]
            ʃ => sh
    """
    )


@pytest.fixture
def extended_sample_changes() -> str:
    return cleandoc(
        """
        Feature type (*consonant, vowel)
        Feature height (*low, mid, high)

        Feature +stressed

        Diacritic ˈ (before) [+stressed] (floating)

        Symbol a [low vowel]
        Symbol u [mid vowel]
        Symbol i [high vowel]

        syllables:
            explicit

        palatalization:
            k => ʃ / _ i

        era1:
            unchanged

        intervocalic-voicing:
            {p, t, k, s} => {b, d, g, z} / [vowel] _ [vowel]

        vowel-raising:
            [+stressed vowel] => [high]

        era2:
            unchanged
            
        ultra-modern:
            [vowel] => [high]

        romanizer-phonetic:
            unchanged

        syllables:
            clear

        romanizer:
            [+stressed vowel] => [*stressed]
            ʃ => sh
    """
    )


@pytest.fixture
def simple_changes(sample_changes: str, tmp_pyconlang: Path) -> Path:
    changes_path = tmp_pyconlang / "changes.lsc"
    changes_path.write_text(sample_changes)

    return changes_path


@pytest.fixture
def simple_lexicon(
    tmp_pyconlang: Path,
    sample_lexicon: str,
) -> Path:
    lexicon_path = tmp_pyconlang / "lexicon.pycl"
    lexicon_path.write_text(sample_lexicon)

    return lexicon_path


@pytest.fixture
def extended_changes(tmp_pyconlang: Path, extended_sample_changes: str) -> Path:
    extended_path = tmp_pyconlang / "ultra-modern.lsc"
    extended_path.write_text(extended_sample_changes)
    return extended_path


@pytest.fixture
def simple_pyconlang(
    tmp_pyconlang: Path,
    simple_changes: Path,
    extended_changes: Path,
    simple_lexicon: Path,
) -> Path:
    return tmp_pyconlang


@pytest.fixture
def metadata(tmp_pyconlang: Path) -> None:  # todo: differently
    """Set up global Metadata.default()"""
    return


@pytest.fixture(autouse=True, scope="function")
def mock_input() -> Generator[PipeInput, None, None]:
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input
