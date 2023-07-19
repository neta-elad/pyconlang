import pytest

from pyconlang.lexurgy import LexurgyClient


@pytest.fixture
def lexurgy_client(simple_changes: None) -> LexurgyClient:
    return LexurgyClient()
