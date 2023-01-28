import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Mapping, Optional

from ..types import ResolvedForm

RULE_PATTERN = r"^([A-Za-z0-9-]+):"


@dataclass
class AffixArranger:
    changes_path: Path

    @cached_property
    def rules(self) -> Mapping[Optional[str], int]:
        rules = []
        for line in self.changes_path.read_text().splitlines():
            if (match := re.match(RULE_PATTERN, line.strip())) is not None:
                rules.append(match.group(1))

        return {rule: i for i, rule in enumerate(rules)} | {None: -1}

    def rearrange(self, form: ResolvedForm) -> ResolvedForm:
        affixes = list(form.affixes)
        affixes.sort(key=lambda affix: self.rules[affix.era_name()])
        return ResolvedForm(stem=form.stem, affixes=tuple(affixes))
