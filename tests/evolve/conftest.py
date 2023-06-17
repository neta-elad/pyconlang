from pathlib import Path

import pytest

from pyconlang.evolve import Evolver
from pyconlang.evolve.arrange import AffixArranger
from pyconlang.evolve.batch import Batcher


@pytest.fixture
def simple_evolver(simple_pyconlang: Path) -> Evolver:
    return Evolver()


@pytest.fixture(scope="session")
def batcher() -> Batcher:
    return Batcher()


@pytest.fixture(scope="session")
def arranger() -> AffixArranger:
    return AffixArranger(["1", "2"])
