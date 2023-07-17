from collections.abc import Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Self

from . import LEXICON_GLOB, LEXICON_PATH
from .cache import path_cached_property
from .domain import Definable, Describable, Fusion, Lang, ResolvedForm, Sentence, Word
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

    @path_cached_property(LEXICON_PATH, LEXICON_GLOB)
    def cached_lexicon(self) -> Lexicon:
        return Lexicon.from_path(LEXICON_PATH)

    @property
    def lexicon(self) -> Lexicon:  # todo: hack for PyCharm
        return self.cached_lexicon

    def resolve_sentence(
        self, sentence: Sentence[Word[Fusion]]
    ) -> Sequence[ResolvedForm]:
        return [self.lexicon.resolve(form, sentence.lang) for form in sentence.words]

    def resolve_and_evolve(self, sentence: Sentence[Word[Fusion]]) -> list[Evolved]:
        return self.evolver.evolve(
            self.resolve_sentence(sentence),
            changes=self.lexicon.changes_for(sentence.lang),
        )

    def evolve_string(self, string: str) -> list[Evolved]:
        return self.resolve_and_evolve(self.parse_sentence(string))

    def gloss_string(self, string: str) -> Sequence[tuple[Evolved, Word[Fusion]]]:
        sentence = self.parse_sentence(string)
        return list(zip(self.resolve_and_evolve(sentence), sentence.words))

    def define_string(self, string: str) -> list[str]:
        sentence = self.parse_definables(string)
        return [self.lexicon.define(record, sentence.lang) for record in sentence.words]

    def resolve_definable_string(self, string: str) -> list[ResolvedForm]:
        sentence = self.parse_definables(string)
        return [
            self.lexicon.resolve_definable(record, sentence.lang)
            for record in sentence.words
        ]

    def resolve_and_evolve_all(self, strings: list[str]) -> None:
        per_lang_sentences: dict[Lang, list[ResolvedForm]] = {}
        for string in strings:
            sentence = self.parse_sentence(string)
            per_lang_sentences.setdefault(sentence.lang, [])
            per_lang_sentences[sentence.lang].extend(self.resolve_sentence(sentence))

        for lang, forms in per_lang_sentences.items():
            self.evolver.evolve(forms, changes=self.lexicon.changes_for(lang))

    def lookup_string(
        self, string: str
    ) -> Sequence[tuple[Word[Fusion], list[tuple[Describable, str]]]]:
        lexicon = self.lexicon
        sentence = self.parse_sentence(string)
        return [(word, lexicon.lookup(word, sentence.lang)) for word in sentence.words]

    def trace_string(self, string: str) -> list[EvolvedWithTrace]:
        sentence = self.parse_sentence(string)
        return self.evolver.trace(
            [self.lexicon.resolve(form, sentence.lang) for form in sentence.words]
        )

    @staticmethod
    def parse_sentence(string: str) -> Sentence[Word[Fusion]]:
        return parse_sentence(string)

    @staticmethod
    def parse_definables(string: str) -> Sentence[Definable]:
        return parse_definables(string)
