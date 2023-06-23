from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Self

from . import LEXICON_PATH
from .cache import path_cached_property
from .domain import Definable, Describable, Entry, Fusion, ResolvedForm, Word
from .evolve import EvolvedWithTrace, Evolver
from .evolve.domain import Evolved
from .lexicon import Lexicon
from .parser import parse_definables, parse_sentence


@dataclass
class Translator:
    evolver: Evolver

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with Evolver.new() as evolver:
            yield cls(evolver)

    @path_cached_property(LEXICON_PATH)
    def lexicon(self) -> Lexicon:
        return Lexicon.from_path(LEXICON_PATH)

    def resolve_and_evolve(self, forms: Sequence[Word[Fusion]]) -> list[Evolved]:
        return self.evolver.evolve([self.lexicon.resolve(form) for form in forms])

    def evolve_string(self, string: str) -> list[Evolved]:
        return self.resolve_and_evolve(self.parse_sentence(string))

    def gloss_string(self, string: str) -> Sequence[tuple[Evolved, Word[Fusion]]]:
        forms = self.parse_sentence(string)
        return list(zip(self.resolve_and_evolve(forms), forms))

    def batch_evolve(self) -> Mapping[Entry, list[Evolved]]:
        forms = []
        entries = {}
        for entry in self.lexicon.entries:
            entry_forms = self.lexicon.resolve_entry(entry)
            entries[entry] = entry_forms
            forms.extend(entry_forms)

        self.evolver.evolve(forms)  # todo cache

        return {
            entry: self.evolver.evolve(entry_forms)
            for entry, entry_forms in entries.items()
        }

    def define_string(self, string: str) -> list[str]:
        return [self.lexicon.define(record) for record in self.parse_definables(string)]

    def resolve_definable_string(self, string: str) -> list[ResolvedForm]:
        return [
            self.lexicon.resolve_definable(record)
            for record in self.parse_definables(string)
        ]

    def resolve_string(self, string: str) -> list[ResolvedForm]:
        return [self.lexicon.resolve(form) for form in self.parse_sentence(string)]

    def lookup_string(
        self, string: str
    ) -> Sequence[tuple[Word[Fusion], list[tuple[Describable, str]]]]:
        lexicon = self.lexicon
        return [(word, lexicon.lookup(word)) for word in self.parse_sentence(string)]

    def trace_string(self, string: str) -> list[EvolvedWithTrace]:
        return self.evolver.trace(
            [self.lexicon.resolve(form) for form in self.parse_sentence(string)]
        )

    def save(self) -> None:
        # todo: cache
        pass
        # self.evolver.save()
        # self.lexicon.save()

    @staticmethod
    def parse_sentence(string: str) -> Sequence[Word[Fusion]]:
        return parse_sentence(string)

    @staticmethod
    def parse_definables(string: str) -> list[Definable]:
        return parse_definables(string)
