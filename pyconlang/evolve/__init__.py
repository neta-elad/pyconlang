import pickle
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path
from subprocess import run
from time import time
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union
from unicodedata import normalize

from .. import PYCONLANG_PATH
from ..checksum import checksum
from ..data import LEXURGY_VERSION
from ..types import Morpheme, ResolvedForm
from .arrange import AffixArranger
from .batch import Batcher, Cache, EvolveQuery, LeafEvolveQuery, NodeEvolveQuery
from .errors import LexurgyError
from .tracer import TraceLine, parse_trace_lines
from .types import Evolved

LEXURGY_PATH = PYCONLANG_PATH / f"lexurgy-{LEXURGY_VERSION}" / "bin" / "lexurgy"
EVOLVE_PATH = PYCONLANG_PATH / "evolve"
CHANGES_PATH = Path("changes.lsc")
CACHE_PATH = EVOLVE_PATH / "cache.pickle"

Evolvable = Union[str, Morpheme, ResolvedForm]

QueryTrace = Tuple[str, List[TraceLine]]
Trace = List[QueryTrace]
EvolvedWithTrace = Tuple[Evolved, Trace]


def get_checksum() -> bytes:
    return checksum(CHANGES_PATH)


@dataclass
class Evolver:
    checksum: bytes = field(default_factory=get_checksum)
    cache: Cache = field(default_factory=dict)
    trace_cache: Dict[EvolveQuery, List[TraceLine]] = field(default_factory=dict)
    batcher: Batcher = field(default_factory=Batcher)

    @cached_property
    def arranger(self) -> AffixArranger:
        return AffixArranger(CHANGES_PATH)

    @classmethod
    def load(cls) -> "Evolver":
        if not CACHE_PATH.exists():
            return cls()

        evolver = pickle.loads(CACHE_PATH.read_bytes())

        if not isinstance(evolver, Evolver):
            return cls()

        evolver.validate_cache()

        return evolver

    def __post_init__(self) -> None:
        EVOLVE_PATH.mkdir(parents=True, exist_ok=True)
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
        return CACHE_PATH.write_bytes(pickle.dumps(self))

    def trace(self, forms: Sequence[Evolvable]) -> List[EvolvedWithTrace]:
        self.evolve(forms, trace=True)

        result = []

        for form in self.normalize_forms(forms):
            query = self.batcher.build_query(form)
            result.append((self.cache[query], self.get_trace(query)))

        return result

    def get_trace(self, query: EvolveQuery) -> Trace:
        if query not in self.trace_cache:
            return []
        query_trace = (query.get_query(self.cache), self.trace_cache[query])
        match query:
            case LeafEvolveQuery():
                return [query_trace]
            case NodeEvolveQuery():
                return (
                    self.get_trace(query.stem)
                    + self.get_trace(query.affix)
                    + [query_trace]
                )

    def evolve(
        self, forms: Sequence[Evolvable], *, trace: bool = False
    ) -> List[Evolved]:
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
                    assert word is not None
                    words.append(word)

                evolved_forms, trace_lines = self.evolve_words(
                    words, start=start, end=end, trace=trace
                )

                for query, evolved in zip(new_queries, evolved_forms):
                    self.cache[query] = evolved
                    if trace:
                        if evolved.proto in trace_lines:
                            self.trace_cache[query] = trace_lines[evolved.proto]

        result: List[Evolved] = []

        for form in resolved_forms:
            evolved_result = self.cache[mapping[form]]
            assert evolved_result is not None
            result.append(evolved_result)

        return result

    def normalize_form(self, form: Evolvable) -> ResolvedForm:
        if isinstance(form, str):
            form = Morpheme(form)
        if isinstance(form, Morpheme):
            form = ResolvedForm(form)

        return self.arranger.rearrange(form)

    def normalize_forms(self, forms: Sequence[Evolvable]) -> Sequence[ResolvedForm]:
        return [self.normalize_form(form) for form in forms]

    @staticmethod
    def evolve_words(
        words: List[str],
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
        trace: bool = False,
    ) -> Tuple[List[Evolved], Mapping[str, List[TraceLine]]]:
        if not words:
            return [], {}

        base_name = f"words-{time():.0f}"

        input_words = EVOLVE_PATH / f"{base_name}.wli"
        input_words.write_text("\n".join(words))

        output_words = EVOLVE_PATH / f"{base_name}_ev.wli"
        output_words.unlink(missing_ok=True)

        phonetic_words = EVOLVE_PATH / f"{base_name}_phonetic.wli"
        phonetic_words.unlink(missing_ok=True)

        trace_file = EVOLVE_PATH / f"{base_name}_trace.wli"
        trace_file.unlink(missing_ok=True)

        args = [
            "sh",
            str(LEXURGY_PATH),
            "sc",
            str(CHANGES_PATH),
            str(input_words),
            "-m",
        ]

        if start is not None:
            args.append("-a")
            args.append(start)

        if end is not None:
            args.append("-b")
            args.append(end)

        if trace:
            args.extend(chain(*zip(["-t"] * len(words), words)))

        result = run(args, capture_output=True, text=True)

        if result.returncode != 0:
            # todo too heuristic?
            stdout = result.stdout.strip().splitlines()
            if len(stdout) > 0:
                raise LexurgyError(
                    result.stdout.strip().splitlines()[-1]
                )
            else:
                raise LexurgyError(result.stderr)

        moderns = normalize("NFD", output_words.read_text().strip()).split("\n")

        if phonetic_words.exists():
            phonetics = normalize("NFD", phonetic_words.read_text()).strip().split("\n")
        else:
            phonetics = moderns

        trace_lines: Mapping[str, List[TraceLine]] = {}
        if trace:
            trace_lines = parse_trace_lines(trace_file.read_text(), words[0])

        return [
            Evolved(proto, modern, phonetic)
            for proto, modern, phonetic in zip(words, moderns, phonetics)
        ], trace_lines

    @staticmethod
    def cleanup() -> None:
        for path in EVOLVE_PATH.iterdir():
            path.unlink()
