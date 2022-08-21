import pytest

from pyconlang.lexicon import Lexicon, parse_lexicon


@pytest.fixture
def parsed_lexicon(sample_lexicon) -> Lexicon:
    return parse_lexicon(sample_lexicon)
