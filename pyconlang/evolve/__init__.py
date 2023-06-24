import random
import shutil
import string
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Self, cast
from unicodedata import normalize

from .. import CHANGES_GLOB, CHANGES_PATH, PYCONLANG_PATH
from ..cache import PersistentDict, path_cached_property
from ..checksum import checksum
from ..domain import Component, Morpheme, ResolvedForm
from ..lexurgy import LexurgyClient
from ..lexurgy.domain import (
    LexurgyErrorResponse,
    LexurgyRequest,
    LexurgyResponse,
    TraceLine,
)
from ..lexurgy.tracer import parse_trace_lines
from .arrange import AffixArranger
from .batch import Batcher, ComponentQuery, CompoundQuery, Query
from .domain import Evolved
from .errors import LexurgyError

EVOLVE_PATH = PYCONLANG_PATH / "evolve"

CACHE_PATH = EVOLVE_PATH / "cache"
SIMPLE_CACHE_PATH = CACHE_PATH / "cache.pickle"
TRACE_CACHE_PATH = CACHE_PATH / "trace_cache.pickle"
CHECKSUM_PATH = CACHE_PATH / "checksum.txt"

Evolvable = str | Morpheme | ResolvedForm

QueryTrace = tuple[str, list[TraceLine]]
Trace = list[QueryTrace]
EvolvedWithTrace = tuple[Evolved, Trace]


def get_checksum() -> bytes:
    return checksum(CHANGES_PATH)


def random_directory() -> Path:
    return EVOLVE_PATH / Path(
        "".join(random.sample(string.ascii_lowercase + string.digits, 5))
    )


@dataclass
class Evolver:
    query_cache: PersistentDict[Query, Evolved]
    trace_cache: PersistentDict[Query, list[TraceLine]]
    batcher: Batcher = field(default_factory=Batcher)
    evolve_directory: Path = field(default_factory=random_directory)

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with cast(
            PersistentDict[Query, Evolved],
            PersistentDict("evolve-cache", [CHANGES_PATH]),
        ) as query_cache, cast(
            PersistentDict[Query, list[TraceLine]],
            PersistentDict("trace-cache", [CHANGES_PATH]),
        ) as trace_cache:
            yield cls(query_cache, trace_cache)

    @path_cached_property(CHANGES_PATH, CHANGES_GLOB)
    def arranger(self) -> AffixArranger:
        return AffixArranger.from_path(CHANGES_PATH)

    @cached_property
    def lexurgy(self) -> LexurgyClient:
        return LexurgyClient()

    def trace(self, forms: Sequence[Evolvable]) -> list[EvolvedWithTrace]:
        self.evolve(forms, trace=True)

        result = []

        for form in self.normalize_forms(forms):
            query = self.batcher.build_query(form)
            result.append((self.query_cache[query], self.get_trace(query)))

        return result

    def get_trace(self, query: Query) -> Trace:
        if query not in self.trace_cache:
            return []
        query_trace = (query.get_query(self.query_cache), self.trace_cache[query])
        match query:
            case ComponentQuery():
                return [query_trace]
            case CompoundQuery():
                return (
                    self.get_trace(query.head)
                    + self.get_trace(query.tail)
                    + [query_trace]
                )

    def evolve(
        self, forms: Sequence[Evolvable], *, trace: bool = False
    ) -> list[Evolved]:
        resolved_forms = self.normalize_forms(forms)

        mapping, layers = self.batcher.build_and_order(resolved_forms)

        for layer in layers:
            segments = Batcher.segment_by_start_end(layer)

            for (start, end), queries in segments.items():
                new_queries = [
                    query
                    for query in queries
                    if query not in self.query_cache
                    or (trace and query not in self.trace_cache)
                ]

                words = []
                for query in new_queries:
                    word = query.get_query(self.query_cache)
                    words.append(word)

                evolved_forms, trace_lines = self.evolve_words(
                    words, start=start, end=end, trace=trace
                )

                for query, evolved in zip(new_queries, evolved_forms):
                    self.query_cache[query] = evolved
                    if trace:
                        if evolved.proto in trace_lines:
                            self.trace_cache[query] = trace_lines[evolved.proto]

        result: list[Evolved] = []

        for form in resolved_forms:
            evolved_result = self.query_cache[mapping[form]]
            assert evolved_result is not None
            result.append(evolved_result)

        return result

    def normalize_form(self, form: Evolvable) -> ResolvedForm:
        if isinstance(form, str):
            form = Morpheme(form)
        if isinstance(form, Morpheme):
            form = Component(form)

        return self.arranger.rearrange(form)

    def normalize_forms(self, forms: Sequence[Evolvable]) -> Sequence[ResolvedForm]:
        return [self.normalize_form(form) for form in forms]

    def evolve_words(
        self,
        words: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        trace: bool = False,
    ) -> tuple[list[Evolved], Mapping[str, list[TraceLine]]]:
        if not words:
            return [], {}

        trace_words = []
        if trace:
            trace_words = words

        request = LexurgyRequest(words, start, end, trace_words)

        response = self.lexurgy.roundtrip(request)

        match response:
            case LexurgyErrorResponse():
                raise LexurgyError(response.message)

            case LexurgyResponse():
                moderns = [normalize("NFD", word) for word in response.words]

                if "phonetic" in response.intermediates:
                    phonetics = [
                        normalize("NFD", word)
                        for word in response.intermediates["phonetic"]
                    ]
                else:
                    phonetics = moderns

                assert len(phonetics) == len(moderns)

                trace_lines: Mapping[str, list[TraceLine]] = {}
                if trace:
                    trace_lines = parse_trace_lines(response.trace_lines, words[0])

                return [
                    Evolved(proto, modern, phonetic)
                    for proto, modern, phonetic in zip(words, moderns, phonetics)
                ], trace_lines

    def cleanup(self) -> None:
        if self.evolve_directory.exists():
            shutil.rmtree(self.evolve_directory)
