from pathlib import Path

import pytest

from pyconlang.lexurgy import LexurgyClient


@pytest.fixture
def lexurgy_client(simple_pyconlang: Path, modern_changes_path: Path) -> LexurgyClient:
    return LexurgyClient(modern_changes_path)
