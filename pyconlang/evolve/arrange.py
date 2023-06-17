import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Callable, Generic, TypeVar

from ..domain import Component, Compound, Joiner, Morpheme, ResolvedForm

RULE_PATTERN = r"^\s*([A-Za-z0-9-]+)\s*:"


T = TypeVar("T")

Ranker = Callable[[Joiner], int]


@dataclass(eq=True, frozen=True)
class FlatJoin(Generic[T]):
    depth: int
    joiner: Joiner
    value: T


FlatJoinRanker = Callable[[tuple[int, FlatJoin[T]]], float]


def flat_join_ranker(ranker: Ranker) -> FlatJoinRanker[T]:
    def rank(pair: tuple[int, FlatJoin[T]]) -> float:
        return ranker(pair[1].joiner) + float(2 ** (-1 - pair[1].depth))

    return rank


FlatTree = tuple[T, list[FlatJoin[T]]]


def flatten(tree: ResolvedForm, depth: int = 0) -> FlatTree[Morpheme]:
    match tree:
        case Component():
            return (tree.form, [])
        case Compound():
            head_first, head_rest = flatten(tree.head, depth + 1)
            tail_first, tail_rest = flatten(tree.tail, depth + 1)
            return (
                head_first,
                head_rest + [FlatJoin(depth, tree.joiner, tail_first)] + tail_rest,
            )


def rebuild(tree: FlatTree[Morpheme], ranker: Ranker) -> ResolvedForm:
    head, rest = tree

    if not rest:
        return Component(head)

    max_joiner_index, max_joiner = max(enumerate(rest), key=flat_join_ranker(ranker))

    before = rest[:max_joiner_index]
    after = rest[(max_joiner_index + 1) :]

    tail_head = max_joiner.value
    joiner = max_joiner.joiner

    head_tree = rebuild((head, before), ranker)
    tail_tree = rebuild((tail_head, after), ranker)

    return Compound(head_tree, joiner, tail_tree)


def rearrange(tree: ResolvedForm, ranker: Ranker) -> ResolvedForm:
    return rebuild(flatten(tree), ranker)


@dataclass
class AffixArranger:
    raw_rules: list[str]

    @classmethod
    def from_path(cls, path: Path) -> "AffixArranger":
        rules = []
        for line in path.read_text().splitlines():
            if (match := re.match(RULE_PATTERN, line.strip())) is not None:
                rules.append(match.group(1))

        return cls(rules)

    @cached_property
    def rules(self) -> Mapping[str | None, int]:
        return {rule: i for i, rule in enumerate(self.raw_rules)} | {None: -1}

    def ranker(self, joiner: Joiner) -> int:
        return self.rules[joiner.era_name()]

    def rearrange(self, form: ResolvedForm) -> ResolvedForm:
        return rearrange(form, self.ranker)

    #     prefixes = form.prefixes
    #     suffixes = form.suffixes
    #
    #     affixes = []
    #
    #     i = j = 0
    #     while i < len(prefixes) and j < len(suffixes):
    #         prefix_era = prefixes[i].era_name()
    #         suffix_era = suffixes[j].era_name()
    #
    #         if self.rules[prefix_era] <= self.rules[suffix_era]:
    #             affixes.append(prefixes[i])
    #             i += 1
    #         else:
    #             affixes.append(suffixes[j])
    #             j += 1
    #
    #     while i < len(prefixes):
    #         affixes.append(prefixes[i])
    #         i += 1
    #
    #     while j < len(suffixes):
    #         affixes.append(suffixes[j])
    #         j += 1
    #
    #     return ArrangedForm(
    #         form.stem, tuple(self.rearrange_affix(affix) for affix in affixes)
    #     )
    #
    # def rearrange_affix(self, affix: ResolvedAffix) -> ArrangedAffix:
    #     form = self.rearrange(affix.form)
    #     return ArrangedAffix(affix.stressed, affix.type, affix.era, form)
