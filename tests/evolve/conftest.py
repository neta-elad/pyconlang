from collections.abc import Generator
from pathlib import Path

import pytest

from pyconlang.evolve import Evolver


@pytest.fixture
def simple_evolver(simple_pyconlang: Path) -> Generator[Evolver, None, None]:
    yield Evolver()
