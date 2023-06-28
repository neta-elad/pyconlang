from pathlib import Path

import pytest

from pyconlang.lexurgy import LexurgyClient


@pytest.fixture
def lexurgy_client(simple_changes: Path) -> LexurgyClient:
    return LexurgyClient()
