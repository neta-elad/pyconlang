import pytest

from pyconlang.evolve import Evolver


@pytest.fixture
def simple_evolver(simple_pyconlang):
    yield Evolver()
