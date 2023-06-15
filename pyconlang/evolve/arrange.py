import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List, Mapping, Optional

from ..types import ResolvedAffix, ResolvedForm
from .types import ArrangedAffix, ArrangedForm

RULE_PATTERN = r"^\s*([A-Za-z0-9-]+)\s*:"


@dataclass
class AffixArranger:
    raw_rules: List[str]

    @classmethod
    def from_path(cls, path: Path) -> "AffixArranger":
        rules = []
        for line in path.read_text().splitlines():
            if (match := re.match(RULE_PATTERN, line.strip())) is not None:
                rules.append(match.group(1))

        return cls(rules)

    @cached_property
    def rules(self) -> Mapping[Optional[str], int]:
        return {rule: i for i, rule in enumerate(self.raw_rules)} | {None: -1}

    def rearrange(self, form: ResolvedForm) -> ArrangedForm:
        prefixes = form.prefixes
        suffixes = form.suffixes

        affixes = []

        i = j = 0
        while i < len(prefixes) and j < len(suffixes):
            prefix_era = prefixes[i].era_name()
            suffix_era = suffixes[j].era_name()

            if self.rules[prefix_era] <= self.rules[suffix_era]:
                affixes.append(prefixes[i])
                i += 1
            else:
                affixes.append(suffixes[j])
                j += 1

        while i < len(prefixes):
            affixes.append(prefixes[i])
            i += 1

        while j < len(suffixes):
            affixes.append(suffixes[j])
            j += 1

        return ArrangedForm(
            form.stem, tuple(self.rearrange_affix(affix) for affix in affixes)
        )

    def rearrange_affix(self, affix: ResolvedAffix) -> ArrangedAffix:
        form = self.rearrange(affix.form)
        return ArrangedAffix(affix.stressed, affix.type, affix.era, form)
