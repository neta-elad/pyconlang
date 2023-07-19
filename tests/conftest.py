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
from pyconlang.metadata import Metadata


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
        scope % : % 'changes/archaic.lsc'
        scope %modern : % 'changes/modern.lsc'
        scope %ultra-modern : %modern 'changes/ultra-modern.lsc'
        
        template &plural $ $.PL # this is a template
        
        affix % .PL *iki@era1 (<big> <pile>) 
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
        
        
        entry %ultra-modern <gravel> <stone>.DIST-PL (n.) gravel (ultra-modern)
        
        entry <gravel>.PL *ka (n.) gravel (plural)
        """
    )


@pytest.fixture
def base_changes() -> str:
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
        """
    )


@pytest.fixture
def romanizer_changes() -> str:
    return cleandoc(
        """
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
def archaic_changes() -> str:
    return cleandoc(
        """
        #include "base.lsc"
        #include "romanizer.lsc"
        """
    )


@pytest.fixture
def modern_base_changes() -> str:
    return cleandoc(
        """
        #include "base.lsc"

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
        """
    )


@pytest.fixture
def modern_changes() -> str:
    return cleandoc(
        """
        #include "modern-base.lsc"
        #include "romanizer.lsc"
        """
    )


@pytest.fixture
def ultra_modern_changes() -> str:
    return cleandoc(
        """
        #include "modern-base.lsc"
        
        ultra-modern:
            [vowel] => [high]

        #include "romanizer.lsc"
        """
    )


@pytest.fixture
def changes_path(tmp_pyconlang: Path) -> Path:
    path = tmp_pyconlang / "changes"
    path.mkdir()
    return path


@pytest.fixture
def base_changes_path(changes_path: Path, base_changes: str) -> Path:
    path = changes_path / "base.lsc"
    path.write_text(base_changes)
    return path


@pytest.fixture
def romanizer_path(changes_path: Path, romanizer_changes: str) -> Path:
    path = changes_path / "romanizer.lsc"
    path.write_text(romanizer_changes)
    return path


@pytest.fixture
def archaic_changes_path(
    changes_path: Path, romanizer_path: Path, archaic_changes: str
) -> Path:
    path = changes_path / "archaic.lsc"
    path.write_text(archaic_changes)
    return path


@pytest.fixture
def modern_base_changes_path(
    changes_path: Path, base_changes_path: Path, modern_base_changes: str
) -> Path:
    path = changes_path / "modern-base.lsc"
    path.write_text(modern_base_changes)
    return path


@pytest.fixture
def modern_changes_path(
    changes_path: Path,
    modern_base_changes_path: Path,
    romanizer_path: Path,
    modern_changes: str,
) -> Path:
    path = changes_path / "modern.lsc"
    path.write_text(modern_changes)
    return path


@pytest.fixture
def ultra_modern_changes_path(
    changes_path: Path,
    modern_base_changes_path: Path,
    romanizer_path: Path,
    ultra_modern_changes: str,
) -> Path:
    path = changes_path / "ultra-modern.lsc"
    path.write_text(ultra_modern_changes)
    return path


@pytest.fixture
def simple_lexicon(
    tmp_pyconlang: Path,
    sample_lexicon: str,
) -> Path:
    lexicon_path = tmp_pyconlang / "lexicon.pycl"
    lexicon_path.write_text(sample_lexicon)

    return lexicon_path


@pytest.fixture
def simple_pyconlang(
    tmp_pyconlang: Path,
    archaic_changes_path: Path,
    modern_changes_path: Path,
    ultra_modern_changes_path: Path,
    simple_lexicon: Path,
    metadata: None,
) -> Path:
    return tmp_pyconlang


@pytest.fixture
def metadata(tmp_pyconlang: Path) -> None:  # todo: differently
    """Set up global Metadata.default()"""
    Metadata.default().scope = "modern"
    Metadata.default().save()
    return


@pytest.fixture
def root_metadata(tmp_pyconlang: Path) -> None:  # todo: differently
    """Set up global Metadata.default()"""
    Metadata.default().scope = ""
    Metadata.default().save()
    return


@pytest.fixture(autouse=True, scope="function")
def mock_input() -> Generator[PipeInput, None, None]:
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input
