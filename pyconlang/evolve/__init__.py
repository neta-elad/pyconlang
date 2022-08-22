import pickle
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import run
from typing import List, Optional, Sequence, Union
from unicodedata import normalize

from .. import PYCONLANG_PATH
from ..checksum import checksum
from ..data import LEXURGY_VERSION
from ..types import Proto, ResolvedForm
from .batch import Cache, build_and_order, segment_by_start_end
from .types import Evolved

LEXURGY_PATH = PYCONLANG_PATH / f"lexurgy-{LEXURGY_VERSION}" / "bin" / "lexurgy"
EVOLVE_PATH = PYCONLANG_PATH / "evolve"
CHANGES_PATH = Path("changes.lsc")
CACHE_PATH = EVOLVE_PATH / "cache.pickle"

Evolvable = Union[str, Proto, ResolvedForm]
Evolvables = Union[Evolvable, Sequence[Evolvable]]


def get_checksum() -> bytes:
    return checksum(CHANGES_PATH)


def normalize_form(form: Evolvable) -> ResolvedForm:
    if isinstance(form, str):
        form = Proto(form)
    if isinstance(form, Proto):
        form = ResolvedForm(form)

    return form


def normalize_forms(forms: Evolvables) -> Sequence[ResolvedForm]:
    if not isinstance(forms, Sequence):
        forms = [forms]

    return [normalize_form(form) for form in forms]


@dataclass
class Evolver:
    checksum: bytes = field(default_factory=get_checksum)
    cache: Cache = field(default_factory=dict)

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
            self.checksum = current_checksum
            return False
        return True

    def save(self) -> int:
        return CACHE_PATH.write_bytes(pickle.dumps(self))

    def evolve_single(self, form: Evolvable) -> Evolved:
        return self.evolve(form)[0]

    def evolve(self, forms: Evolvables) -> List[Evolved]:
        resolved_forms = normalize_forms(forms)

        mapping, layers = build_and_order(resolved_forms)

        for layer in layers:
            segments = segment_by_start_end(layer)

            for (start, end), queries in segments.items():
                new_queries = [query for query in queries if query not in self.cache]

                words = []
                for query in new_queries:
                    word = query.get_query(self.cache)
                    assert word is not None
                    words.append(word)

                evolved_forms = self.evolve_words(words, start=start, end=end)

                for query, evolved in zip(new_queries, evolved_forms):
                    self.cache[query] = evolved

        result: List[Evolved] = []

        for form in resolved_forms:
            evolved_result = self.cache[mapping[form]]
            assert evolved_result is not None
            result.append(evolved_result)

        return result

    @staticmethod
    def evolve_words(
        words: List[str],
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Evolved]:
        if not words:
            return []

        input_words = EVOLVE_PATH / "words.wli"
        input_words.write_text("\n".join(words))

        output_words = EVOLVE_PATH / "words_ev.wli"
        output_words.unlink(missing_ok=True)

        phonetic_words = EVOLVE_PATH / "words_phonetic.wli"
        phonetic_words.unlink(missing_ok=True)

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

        run(
            args,
            check=True,
            capture_output=True,
        )

        moderns = normalize("NFD", output_words.read_text().strip()).split("\n")

        if phonetic_words.exists():
            phonetics = normalize("NFD", phonetic_words.read_text()).strip().split("\n")
        else:
            phonetics = moderns

        return [
            Evolved(proto, modern, phonetic)
            for proto, modern, phonetic in zip(words, moderns, phonetics)
        ]
