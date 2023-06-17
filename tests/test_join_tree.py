from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from pyconlang.domain import BranchJoin, Joiner, JoinTree, LeafJoin, Rule

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
        return ranker(pair[1].joiner) + float(2 ** (-pair[1].depth))

    return rank


FlatTree = tuple[T, list[FlatJoin[T]]]


def flatten(tree: JoinTree[T], depth: int = 0) -> FlatTree[T]:
    match tree:
        case LeafJoin():
            return (tree.value, [])
        case BranchJoin():
            head_first, head_rest = flatten(tree.head, depth + 1)
            tail_first, tail_rest = flatten(tree.tail, depth + 1)
            return (
                head_first,
                head_rest + [FlatJoin(depth, tree.joiner, tail_first)] + tail_rest,
            )


def rebuild(tree: FlatTree[T], ranker: Ranker) -> JoinTree[T]:
    head, rest = tree

    if not rest:
        return LeafJoin(head)

    max_joiner_index, max_joiner = max(enumerate(rest), key=flat_join_ranker(ranker))

    before = rest[:max_joiner_index]
    after = rest[(max_joiner_index + 1) :]

    tail_head = max_joiner.value
    joiner = max_joiner.joiner

    head_tree = rebuild((head, before), ranker)
    tail_tree = rebuild((tail_head, after), ranker)

    return BranchJoin(head_tree, joiner, tail_tree)


def rearrange(tree: JoinTree[T], ranker: Ranker) -> JoinTree[T]:
    return rebuild(flatten(tree), ranker)


def my_ranker(joiner: Joiner) -> int:
    if joiner.era is None:
        return 0

    return len(joiner.era.name)


def test_flatten() -> None:
    assert flatten(LeafJoin("a")) == ("a", [])
    assert flatten(BranchJoin(LeafJoin("a"), Joiner.head(), LeafJoin("b"))) == (
        "a",
        [FlatJoin(0, Joiner.head(), "b")],
    )
    assert flatten(
        BranchJoin(
            BranchJoin(LeafJoin("a"), Joiner.head(Rule("ii")), LeafJoin("b")),
            Joiner.head(Rule("i")),
            LeafJoin("c"),
        )
    ) == (
        "a",
        [
            FlatJoin(1, Joiner.head(Rule("ii")), "b"),
            FlatJoin(0, Joiner.head(Rule("i")), "c"),
        ],
    )


def test_rearrange() -> None:
    assert rearrange(
        BranchJoin(LeafJoin("a"), Joiner.head(), LeafJoin("b")), my_ranker
    ) == BranchJoin(LeafJoin("a"), Joiner.head(), LeafJoin("b"))

    assert rearrange(
        BranchJoin(
            BranchJoin(LeafJoin("a"), Joiner.head(Rule("ii")), LeafJoin("b")),
            Joiner.head(Rule("i")),
            LeafJoin("c"),
        ),
        my_ranker,
    ) == BranchJoin(
        LeafJoin("a"),
        Joiner.head(Rule("ii")),
        BranchJoin(LeafJoin("b"), Joiner.head(Rule("i")), LeafJoin("c")),
    )

    assert rearrange(
        BranchJoin(
            BranchJoin(LeafJoin("a"), Joiner.head(Rule("i")), LeafJoin("b")),
            Joiner.head(Rule("i")),
            LeafJoin("c"),
        ),
        my_ranker,
    ) == BranchJoin(
        BranchJoin(LeafJoin("a"), Joiner.head(Rule("i")), LeafJoin("b")),
        Joiner.head(Rule("i")),
        LeafJoin("c"),
    )
