from contextlib import contextmanager
from typing import Generator

from pyconlang.domain import (
    Compound,
    DefaultFusion,
    DefaultSentence,
    DefaultWord,
    Joiner,
    Sentence,
    Tags,
)
from pyconlang.metadata import Metadata


def default_compound(
    head: DefaultWord, joiner: Joiner, tail: DefaultWord
) -> Compound[DefaultFusion]:
    return Compound(head, joiner, tail)


def default_sentence(tags: Tags, words: list[DefaultWord]) -> DefaultSentence:
    return Sentence(tags, words)


@contextmanager
def metadata_as(metadata: Metadata) -> Generator[None, None, None]:
    original = getattr(Metadata, "default")
    setattr(Metadata, "default", lambda: metadata)
    yield
    setattr(Metadata, "default", original)
