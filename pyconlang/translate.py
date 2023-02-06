from dataclasses import dataclass, field
from typing import List, Mapping, Sequence, Tuple

from .evolve import EvolvedWithTrace, Evolver
from .evolve.types import Evolved
from .lexicon import Lexicon
from .parser import parse_definables, parse_sentence
from .types import Definable, Describable, Entry, ResolvedForm, Unit


@dataclass
class Translator:
    lexicon_checksum: bytes = field(default_factory=Lexicon.checksum)
    lexicon: Lexicon = field(default_factory=Lexicon.from_path)
    evolver: Evolver = field(default_factory=Evolver.load)

    def resolve_and_evolve(self, forms: Sequence[Unit]) -> List[Evolved]:
        return self.evolver.evolve([self.lexicon.resolve(form) for form in forms])

    def evolve_string(self, string: str) -> List[Evolved]:
        return self.resolve_and_evolve(self.parse_sentence(string))

    def gloss_string(self, string: str) -> Sequence[Tuple[Evolved, Unit]]:
        forms = self.parse_sentence(string)
        return list(zip(self.resolve_and_evolve(forms), forms))

    def batch_evolve(self) -> Mapping[Entry, List[Evolved]]:
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

    def define_string(self, string: str) -> List[str]:
        return [self.lexicon.define(record) for record in self.parse_definables(string)]

    def resolve_string(self, string: str) -> List[ResolvedForm]:
        return [self.lexicon.resolve(form) for form in self.parse_sentence(string)]

    def lookup_string(
        self, string: str
    ) -> Sequence[Tuple[Unit, List[Tuple[Describable, str]]]]:
        lexicon = self.lexicon
        return [(form, lexicon.lookup(form)) for form in self.parse_sentence(string)]

    def trace_string(self, string: str) -> List[EvolvedWithTrace]:
        return self.evolver.trace(
            [self.lexicon.resolve(form) for form in self.parse_sentence(string)]
        )

    def validate_cache(self) -> bool:
        evolver_cache = self.evolver.validate_cache()

        if Lexicon.checksum() != self.lexicon_checksum:
            self.lexicon = Lexicon.from_path()
            self.lexicon_checksum = Lexicon.checksum()
            return False
        return evolver_cache

    def save(self) -> None:
        self.evolver.save()
        # self.lexicon.save()

    @staticmethod
    def parse_sentence(string: str) -> Sequence[Unit]:
        return parse_sentence(string)

    @staticmethod
    def parse_definables(string: str) -> List[Definable]:
        return parse_definables(string)
