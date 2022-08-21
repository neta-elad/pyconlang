from dataclasses import dataclass, field
from typing import List, Mapping

from .evolve import Evolved, Evolver
from .lexicon import Lexicon
from .lexicon.parser import parse_sentence
from .types import Entry, Form


@dataclass
class Translator:
    lexicon: Lexicon = field(default_factory=Lexicon.from_path)
    evolver: Evolver = field(default_factory=Evolver.load)

    def evolve(self, form: Form) -> Evolved:
        return self.evolver.evolve_single(self.lexicon.resolve(form))

    def evolve_string(self, string: str) -> List[Evolved]:
        return [self.evolve(form) for form in parse_sentence(string)]

    def evolve_all(self, entry: Entry) -> List[Evolved]:
        return [
            self.evolver.evolve_single(self.lexicon.substitute(var, entry.form))
            for var in self.lexicon.get_vars(entry.template)
        ]

    def batch_evolve(self) -> Mapping[Entry, List[Evolved]]:
        # todo optimize
        return {entry: self.evolve_all(entry) for entry in self.lexicon.entries}
