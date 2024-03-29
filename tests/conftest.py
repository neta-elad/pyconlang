import os
from collections.abc import Generator
from dataclasses import replace
from inspect import cleandoc
from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output import DummyOutput

from pyconlang import LEXICON_PATH, SRC_PATH
from pyconlang.cli import init
from pyconlang.config import Config, config, config_as, file_config


@pytest.fixture
def cd_tmp_path(tmp_path: Path) -> Generator[Path, None, None]:
    os.chdir(tmp_path)
    yield tmp_path


@pytest.fixture
def tmp_pyconlang(cd_tmp_path: Path) -> Generator[Path, None, None]:
    assert init.callback is not None
    init.callback(cd_tmp_path, "TestLang", "Mr. Tester", False, False)

    with file_config():
        yield cd_tmp_path


@pytest.fixture
def sample_lexicon() -> str:
    return cleandoc(
        """
        scope % : % 'src/archaic.lsc' @era1
        scope %modern : % 'src/modern.lsc'
        scope %ultra-modern : %modern 'src/ultra-modern.lsc'
        
        template &plural $ $.PL # this is a template
        
        affix % .PL *iki@era1 (<big> <pile>) 
            plural for inanimate
        affix % .COL *ma collective
        
        affix %modern .LARGE *ha large object
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
        
        entry %modern <stone> *kapa (n.) stone, pebble
        
        entry <gravel> <stone>.PL (n.) gravel
        
        entry %ultra-modern <council> % <big>.PL (n.) council
        
        entry % <big>.PL *sama (adj.) large people
        
        entry %ultra-modern <gravel> <stone>.DIST-PL (n.) gravel
        
        entry <gravel>.PL *ka (n.) gravel (plural)
        
        affix % 1SG. *po 1sg
        affix % 2SG. *mo 2sg
        entry 1SG.<eat> *ta (v.) I eat
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
            [+stressed vowel] => [*stressed]
            ʃ => sh
        """
    )


@pytest.fixture
def archaic_changes() -> str:
    return cleandoc(
        """
        #include "base.lsc"
        
        romanizer-archaic-phonetic:
            unchanged
            
        romanizer-archaic:
        #include "romanizer.lsc"
        """
    )


@pytest.fixture
def modern_changes() -> str:
    return cleandoc(
        """
        #include "archaic.lsc"

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
        
        romanizer-modern-phonetic:
            unchanged
            
        romanizer-modern:
        #include "romanizer.lsc"
        """
    )


@pytest.fixture
def ultra_modern_changes() -> str:
    return cleandoc(
        """
        #include "modern.lsc"
        
        ultra-modern:
            [vowel] => [high]

        romanizer-ultra-modern-phonetic:
            unchanged
            
        romanizer-ultra-modern:
        #include "romanizer.lsc"
        """
    )


@pytest.fixture
def changes_path(tmp_pyconlang: Path) -> Path:
    path = tmp_pyconlang / SRC_PATH
    path.mkdir(parents=True, exist_ok=True)
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
    changes_path: Path,
    base_changes_path: Path,
    romanizer_path: Path,
    archaic_changes: str,
) -> Path:
    path = changes_path / "archaic.lsc"
    path.write_text(archaic_changes)
    return path


@pytest.fixture
def modern_changes_path(
    changes_path: Path,
    archaic_changes_path: Path,
    romanizer_path: Path,
    modern_changes: str,
) -> Path:
    path = changes_path / "modern.lsc"
    path.write_text(modern_changes)
    return path


@pytest.fixture
def ultra_modern_changes_path(
    changes_path: Path,
    modern_changes_path: Path,
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
    lexicon_path = tmp_pyconlang / LEXICON_PATH
    lexicon_path.write_text(sample_lexicon)

    return lexicon_path


@pytest.fixture
def simple_pyconlang(
    tmp_pyconlang: Path,
    archaic_changes_path: Path,
    modern_changes_path: Path,
    ultra_modern_changes_path: Path,
    simple_lexicon: Path,
    modern_config: Config,
) -> Path:
    return tmp_pyconlang


@pytest.fixture
def default_config(tmp_pyconlang: Path) -> Config:
    return config()


@pytest.fixture
def modern_config(
    default_config: Config,
) -> Generator[Config, None, None]:
    """Set up global config() with scope = modern"""
    modern_config = replace(default_config, scope="modern")
    with config_as(modern_config):
        yield modern_config


@pytest.fixture
def root_config(
    default_config: Config,
) -> Generator[Config, None, None]:
    """Set up global config() with scope = <root>"""
    root_config = replace(default_config, scope="")
    with config_as(root_config):
        yield root_config


@pytest.fixture(autouse=True, scope="function")
def mock_input() -> Generator[PipeInput, None, None]:
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input
