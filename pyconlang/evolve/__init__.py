import pickle
import random
import shutil
import string
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from unicodedata import normalize

from .. import CHANGES_PATH, PYCONLANG_PATH
from ..cache import path_cached_property
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
from .batch import Batcher, Cache, ComponentQuery, CompoundQuery, Query
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
    checksum: bytes = field(default_factory=get_checksum)
    cache: Cache = field(default_factory=dict)
    trace_cache: dict[Query, list[TraceLine]] = field(default_factory=dict)
    batcher: Batcher = field(default_factory=Batcher)
    evolve_directory: Path = field(default_factory=random_directory)

    @path_cached_property(CHANGES_PATH)
    def arranger(self) -> AffixArranger:
        return AffixArranger.from_path(CHANGES_PATH)

    @cached_property
    def lexurgy(self) -> LexurgyClient:
        return LexurgyClient()

    @classmethod
    def load(cls) -> "Evolver":
        if not all(
            [
                path.exists()
                for path in [SIMPLE_CACHE_PATH, TRACE_CACHE_PATH, CHECKSUM_PATH]
            ]
        ):
            return cls()

        cached_checksum = pickle.loads(CHECKSUM_PATH.read_bytes())
        cache = pickle.loads(SIMPLE_CACHE_PATH.read_bytes())
        trace_cache = pickle.loads(TRACE_CACHE_PATH.read_bytes())

        evolver = cls(cached_checksum, cache, trace_cache)

        evolver.validate_cache()

        return evolver

    def __post_init__(self) -> None:
        self.validate_cache()

    def validate_cache(self) -> bool:
        current_checksum = get_checksum()
        if self.checksum != current_checksum:
            self.cache = {}
            self.trace_cache = {}
            self.checksum = current_checksum
            return False
        return True

    def save(self) -> int:
        self.cleanup()
        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        bytes_written = TRACE_CACHE_PATH.write_bytes(pickle.dumps(self.trace_cache))
        bytes_written += SIMPLE_CACHE_PATH.write_bytes(pickle.dumps(self.cache))
        bytes_written += CHECKSUM_PATH.write_bytes(pickle.dumps(self.checksum))
        return bytes_written

    def trace(self, forms: Sequence[Evolvable]) -> list[EvolvedWithTrace]:
        self.evolve(forms, trace=True)

        result = []

        for form in self.normalize_forms(forms):
            query = self.batcher.build_query(form)
            result.append((self.cache[query], self.get_trace(query)))

        return result

    def get_trace(self, query: Query) -> Trace:
        if query not in self.trace_cache:
            return []
        query_trace = (query.get_query(self.cache), self.trace_cache[query])
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
                    if query not in self.cache
                    or (trace and query not in self.trace_cache)
                ]

                words = []
                for query in new_queries:
                    word = query.get_query(self.cache)
                    words.append(word)

                evolved_forms, trace_lines = self.evolve_words(
                    words, start=start, end=end, trace=trace
                )

                for query, evolved in zip(new_queries, evolved_forms):
                    self.cache[query] = evolved
                    if trace:
                        if evolved.proto in trace_lines:
                            self.trace_cache[query] = trace_lines[evolved.proto]

        result: list[Evolved] = []

        for form in resolved_forms:
            evolved_result = self.cache[mapping[form]]
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

        debug_words = []
        if trace:
            debug_words = words

        request = LexurgyRequest(words, start, end, debug_words)

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
