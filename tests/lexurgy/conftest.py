from collections.abc import Generator
from pathlib import Path

import pytest

from pyconlang.lexurgy import LexurgyClient


@pytest.fixture
def lexurgy_client(simple_changes: Path) -> Generator[LexurgyClient, None, None]:
    yield LexurgyClient()
