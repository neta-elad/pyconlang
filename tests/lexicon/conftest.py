import pytest

from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.parser import lexicon


@pytest.fixture
def parsed_lexicon(sample_lexicon) -> Lexicon:
    return lexicon.parse_string(sample_lexicon)[0]
