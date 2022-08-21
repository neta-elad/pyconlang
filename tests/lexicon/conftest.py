import pytest

from pyconlang.lexicon import Lexicon


@pytest.fixture
def parsed_lexicon(sample_lexicon) -> Lexicon:
    return Lexicon.from_string(sample_lexicon)
