from collections.abc import Mapping
from pathlib import Path
from typing import Generator, Protocol

import pytest

from pyconlang.evolve import Evolver
from pyconlang.evolve.arrange import AffixArranger
from pyconlang.evolve.batch import Batcher
from pyconlang.evolve.domain import Evolved
from pyconlang.lexurgy.domain import TraceLine


class EvolveWords(Protocol):
    def __call__(
        self,
        words: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        trace: bool = False,
    ) -> tuple[list[Evolved], Mapping[str, list[TraceLine]]]:
        ...


@pytest.fixture
def simple_evolver(simple_pyconlang: Path) -> Generator[Evolver, None, None]:
    with Evolver.new() as evolver:
        yield evolver


@pytest.fixture
def modern_evolve(simple_evolver: Evolver, modern_changes_path: Path) -> EvolveWords:
    def evolve(
        words: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        trace: bool = False,
    ) -> tuple[list[Evolved], Mapping[str, list[TraceLine]]]:
        return simple_evolver.evolve_words(
            words, start=start, end=end, trace=trace, changes=modern_changes_path
        )

    return evolve


@pytest.fixture
def ultra_modern_evolve(
    simple_evolver: Evolver, ultra_modern_changes_path: Path
) -> EvolveWords:
    def evolve(
        words: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        trace: bool = False,
    ) -> tuple[list[Evolved], Mapping[str, list[TraceLine]]]:
        return simple_evolver.evolve_words(
            words, start=start, end=end, trace=trace, changes=ultra_modern_changes_path
        )

    return evolve


@pytest.fixture
def batcher(metadata: None) -> Batcher:
    return Batcher()


@pytest.fixture(scope="session")
def arranger() -> AffixArranger:
    return AffixArranger(["1", "2"])
