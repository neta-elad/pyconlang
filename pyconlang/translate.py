from dataclasses import dataclass, field
from typing import List, Mapping

from .evolve import Evolver
from .evolve.types import Evolved
from .lexicon import Lexicon
from .lexicon.parser import parse_sentence
from .types import Entry, Form


@dataclass
class Translator:
    lexicon_checksum: bytes = field(default_factory=Lexicon.checksum)
    lexicon: Lexicon = field(default_factory=Lexicon.from_path)
    evolver: Evolver = field(default_factory=Evolver.load)

    def evolve(self, form: Form) -> Evolved:
        return self.evolver.evolve_single(self.lexicon.resolve(form))

    def evolve_string(self, string: str) -> List[Evolved]:
        return self.evolver.evolve(
            [self.lexicon.resolve(form) for form in parse_sentence(string)]
        )

    def evolve_entry(self, entry: Entry) -> List[Evolved]:
        return [
            self.evolver.evolve_single(form)
            for form in self.lexicon.resolve_entry(entry)
        ]

    def batch_evolve(self) -> Mapping[Entry, List[Evolved]]:
        forms = []
        entries = {}
        for entry in self.lexicon.entries:
            entry_forms = self.lexicon.resolve_entry(entry)
            entries[entry] = entry_forms
            forms.extend(entry_forms)

        self.evolver.evolve(forms)  # cache

        return {
            entry: self.evolver.evolve(entry_forms)
            for entry, entry_forms in entries.items()
        }

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