from dataclasses import dataclass, field
from pathlib import Path
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import List, Optional

from . import PYCONLANG_PATH
from .data import LEXURGY_VERSION
from .ipa import remove_primary_stress
from .types import AffixType, Proto, ResolvedForm, Rule

LEXURGY_PATH = PYCONLANG_PATH / f"lexurgy-{LEXURGY_VERSION}" / "bin" / "lexurgy"


@dataclass
class LexurgySession:
    args: List[str] = field(default_factory=list)
    words: List[str] = field(default_factory=list)

    def clear(self) -> None:
        self.words = []

    def add_word(self, word: str) -> None:
        self.words.append(word)

    def evolve(self) -> List[str]:
        return self.evolve_words(self.words)

    def evolve_word(self, word: str) -> str:
        return self.evolve_words([word])[0]

    def evolve_words(self, words: List[str]) -> List[str]:
        with TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            input_words = dir_path / "words.wli"
            input_words.write_text("\n".join(words))
            check_call(
                [
                    "sh",
                    str(LEXURGY_PATH),
                    "sc",
                    "changes.lsc",
                    str(input_words),
                ]
                + self.args
            )

            output_words = dir_path / "words_ev.wli"
            return output_words.read_text().strip().split("\n")


def evolve_word(
    word: str, *, start: Optional[Rule] = None, end: Optional[Rule] = None
) -> str:
    args = []
    if start is not None:
        args.extend(["-a", start.name])
    if end is not None:
        args.extend(["-b", end.name])
    return LexurgySession(args).evolve_word(word)


def evolve_proto(proto: Proto, end: Optional[Rule] = None) -> str:
    return evolve_word(proto.form, start=proto.era, end=end)


def evolve(fusion: ResolvedForm) -> str:
    form = fusion.stem
    for affix in fusion.affixes:
        if affix.era is not None and form.era != affix.era:
            evolved = evolve_proto(form, affix.era)
            evolved_affix = evolve(affix.form)

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


def glom_at(prefix: str, suffix: str, rule: Rule, stressed_suffix: bool = False) -> str:
    evolved_prefix = evolve_word(prefix, end=rule)
    evolved_suffix = evolve_word(suffix, end=rule)

    if stressed_suffix:
        evolved_prefix = remove_primary_stress(evolved_prefix)
    else:
        evolved_suffix = remove_primary_stress(evolved_suffix)

    return evolve_word(evolved_prefix + evolved_suffix, start=rule)
