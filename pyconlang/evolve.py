from dataclasses import dataclass, field
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import List, Optional
from unicodedata import normalize

from . import PYCONLANG_PATH
from .data import LEXURGY_VERSION
from .ipa import remove_primary_stress
from .types import AffixType, Proto, ResolvedForm, Rule

LEXURGY_PATH = PYCONLANG_PATH / f"lexurgy-{LEXURGY_VERSION}" / "bin" / "lexurgy"


@dataclass(eq=True, frozen=True)
class Evolved:
    proto: str
    modern: str
    phonetic: str


@dataclass
class LexurgySession:
    args: List[str] = field(default_factory=list)
    words: List[str] = field(default_factory=list)

    def clear(self) -> None:
        self.words = []

    def add_word(self, word: str) -> None:
        self.words.append(word)

    def evolve(self) -> List[Evolved]:
        return self.evolve_words(self.words)

    def evolve_word(self, word: str) -> Evolved:
        return self.evolve_words([word])[0]

    def evolve_words(self, words: List[str]) -> List[Evolved]:
        with TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            input_words = dir_path / "words.wli"
            input_words.write_text("\n".join(words))
            run(
                ["sh", str(LEXURGY_PATH), "sc", "changes.lsc", str(input_words), "-m"]
                + self.args,
                check=True,
                capture_output=True,
            )

            output_words = dir_path / "words_ev.wli"
            phonetic_words = dir_path / "words_phonetic.wli"

            moderns = normalize("NFD", output_words.read_text().strip()).split("\n")

            if phonetic_words.exists():
                phonetics = (
                    normalize("NFD", phonetic_words.read_text()).strip().split("\n")
                )
            else:
                phonetics = moderns

            return [
                Evolved(proto, modern, phonetic)
                for proto, modern, phonetic in zip(words, moderns, phonetics)
            ]


def evolve_word(
    word: str, *, start: Optional[Rule] = None, end: Optional[Rule] = None
) -> Evolved:
    args = []
    if start is not None:
        args.extend(["-a", start.name])
    if end is not None:
        args.extend(["-b", end.name])
    return LexurgySession(args).evolve_word(word)


def evolve_proto(proto: Proto, end: Optional[Rule] = None) -> Evolved:
    return evolve_word(proto.form, start=proto.era, end=end)


def evolve(fusion: ResolvedForm) -> Evolved:
    form = fusion.stem
    for affix in fusion.affixes:
        if affix.era is not None and form.era != affix.era:
            evolved = evolve_proto(form, affix.era).phonetic
            evolved_affix = evolve(affix.form).phonetic

            form = Proto(fuse(evolved, evolved_affix, affix.affix.type), affix.era)
        else:
            form = Proto(
                fuse(form.form, affix.form.stem.form, affix.affix.type), form.era
            )

    return evolve_proto(form)


def fuse(stem: str, affix: str, affix_type: AffixType) -> str:
    if affix_type is AffixType.PREFIX:
        return affix + stem
    else:
        return stem + affix


def glom_at(
    prefix: str, suffix: str, rule: Rule, stressed_suffix: bool = False
) -> Evolved:
    evolved_prefix = evolve_word(prefix, end=rule).phonetic
    evolved_suffix = evolve_word(suffix, end=rule).phonetic

    if stressed_suffix:
        evolved_prefix = remove_primary_stress(evolved_prefix)
    else:
        evolved_suffix = remove_primary_stress(evolved_suffix)

    return evolve_word(evolved_prefix + evolved_suffix, start=rule)
