from pathlib import Path
from typing import Generator

import pytest

from pyconlang.evolve import Evolver
from pyconlang.evolve.arrange import AffixArranger
from pyconlang.evolve.batch import Batcher


@pytest.fixture
def simple_evolver(simple_pyconlang: Path) -> Generator[Evolver, None, None]:
    with Evolver.new() as evolver:
        yield evolver


@pytest.fixture
def batcher(metadata: None) -> Batcher:
    return Batcher()


@pytest.fixture(scope="session")
def arranger() -> AffixArranger:
    return AffixArranger(["1", "2"])
