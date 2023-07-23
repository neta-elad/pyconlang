from pyconlang.domain import (
    Compound,
    DefaultFusion,
    DefaultSentence,
    DefaultWord,
    Joiner,
    Sentence,
    Tags,
)


def default_compound(
    head: DefaultWord, joiner: Joiner, tail: DefaultWord
) -> Compound[DefaultFusion]:
    return Compound(head, joiner, tail)


def default_sentence(tags: Tags, words: list[DefaultWord]) -> DefaultSentence:
    return Sentence(tags, words)
