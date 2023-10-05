from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import MutableMapping, Self, cast
from unicodedata import normalize

from .. import CHANGES_GLOB, CHANGES_PATH
from ..cache import PersistentDict
from ..domain import ResolvedForm
from ..lexurgy import LexurgyClient
from ..lexurgy.domain import (
    LexurgyErrorResponse,
    LexurgyRequest,
    LexurgyResponse,
    TraceLine,
)
from ..lexurgy.tracer import parse_trace_lines
from ..strings import remove_syllable_break
from .arrange import AffixArranger, arranger_for
from .batch import Batcher, ComponentQuery, CompoundQuery, Query, segment_by_start_end
from .domain import Evolved
from .errors import LexurgyError
from .tuple_mapping_view import TupleMappingView

QueryTrace = tuple[str, list[TraceLine]]
Trace = list[QueryTrace]
EvolvedWithTrace = tuple[Evolved, Trace]


@dataclass
class Evolver:
    query_cache: PersistentDict[tuple[Path, Query], Evolved]
    trace_cache: PersistentDict[tuple[Path, Query], list[TraceLine]]
    batcher: Batcher = field(default_factory=Batcher)

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with cast(
            PersistentDict[tuple[Path, Query], Evolved],
            PersistentDict("evolve-cache", [CHANGES_PATH, CHANGES_GLOB]),
        ) as query_cache, cast(
            PersistentDict[tuple[Path, Query], list[TraceLine]],
            PersistentDict("trace-cache", [CHANGES_PATH, CHANGES_GLOB]),
        ) as trace_cache:
            yield cls(query_cache, trace_cache)

    def arranger(self, changes: Path) -> AffixArranger:
        return arranger_for(changes)

    def lexurgy(self, changes: Path) -> LexurgyClient:
        return LexurgyClient.for_changes(changes)

    def trace(
        self, forms: Sequence[ResolvedForm], *, changes: Path
    ) -> list[EvolvedWithTrace]:
        self.evolve(forms, trace=True, changes=changes)

        result = []

        cache: MutableMapping[Query, Evolved] = TupleMappingView(
            self.query_cache, changes
        )

        for form in self.rearrange_forms(forms, changes):
            query = self.batcher.builder(self.arranger(changes)).build_query(form)
            result.append((cache[query], self.get_trace(query, changes=changes)))

        return result

    def get_trace(self, query: Query, *, changes: Path) -> Trace:
        trace_cache: Mapping[Query, list[TraceLine]] = TupleMappingView(
            self.trace_cache, changes
        )
        if query not in trace_cache:
            return []
        query_trace = (
            query.get_query(TupleMappingView(self.query_cache, changes)),
            self.trace_cache[(changes, query)],
        )
        match query:
            case ComponentQuery():
                return [query_trace]
            case CompoundQuery():
                return (
                    self.get_trace(query.head, changes=changes)
                    + self.get_trace(query.tail, changes=changes)
                    + [query_trace]
                )

    def evolve(
        self,
        forms: Sequence[ResolvedForm],
        *,
        trace: bool = False,
        changes: Path,
    ) -> list[Evolved]:
        cache = TupleMappingView(self.query_cache, changes)
        resolved_forms = self.rearrange_forms(forms, changes)

        mapping, layers = self.batcher.builder(self.arranger(changes)).build_and_order(
            resolved_forms
        )

        for layer in layers:
            segments = segment_by_start_end(layer)

            for (start, end), queries in segments.items():
                new_queries = [
                    query
                    for query in queries
                    if (changes, query) not in self.query_cache
                    or (trace and (changes, query) not in self.trace_cache)
                ]

                words = []
                for query in new_queries:
                    word = query.get_query(cache)
                    words.append(word)

                evolved_forms, trace_lines = self.evolve_words(
                    words, start=start, end=end, trace=trace, changes=changes
                )

                for query, evolved in zip(new_queries, evolved_forms):
                    self.query_cache[(changes, query)] = evolved
                    if trace:
                        if evolved.proto in trace_lines:
                            self.trace_cache[(changes, query)] = trace_lines[
                                evolved.proto
                            ]

        result: list[Evolved] = []

        for form in resolved_forms:
            evolved_result = self.query_cache[(changes, mapping[form])]
            assert evolved_result is not None
            result.append(evolved_result)

        return result

    def rearrange(self, form: ResolvedForm, changes: Path) -> ResolvedForm:
        return self.arranger(changes).rearrange(form)

    def rearrange_forms(
        self, forms: Sequence[ResolvedForm], changes: Path
    ) -> Sequence[ResolvedForm]:
        return [self.rearrange(form, changes) for form in forms]

    def evolve_words(
        self,
        words: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        trace: bool = False,
        changes: Path,
    ) -> tuple[list[Evolved], Mapping[str, list[TraceLine]]]:
        if not words:
            return [], {}

        trace_words = []
        if trace:
            trace_words = words

        request = LexurgyRequest(words, start, end, trace_words)

        response = self.lexurgy(changes).roundtrip(request)

        match response:
            case LexurgyErrorResponse():
                raise LexurgyError(response.message)

            case LexurgyResponse():
                modern_name = changes.stem

                if modern_name in response.intermediates:
                    moderns = [
                        normalize("NFD", word)
                        for word in response.intermediates[modern_name]
                    ]
                else:
                    moderns = [normalize("NFD", word) for word in response.words]

                phonetic_name = f"{modern_name}-phonetic"
                if phonetic_name in response.intermediates:
                    phonetics = [
                        normalize("NFD", word)
                        for word in response.intermediates[phonetic_name]
                    ]
                elif "phonetic" in response.intermediates:
                    phonetics = [
                        normalize("NFD", word)
                        for word in response.intermediates["phonetic"]
                    ]
                else:
                    phonetics = moderns

                moderns = list(map(remove_syllable_break, moderns))

                assert len(phonetics) == len(moderns)

                trace_lines: Mapping[str, list[TraceLine]] = {}
                if trace:
                    trace_lines = parse_trace_lines(response.trace_lines, words[0])

                return [
                    Evolved(proto, modern, phonetic)
                    for proto, modern, phonetic in zip(words, moderns, phonetics)
                ], trace_lines
