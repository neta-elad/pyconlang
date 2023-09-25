from contextlib import contextmanager
from dataclasses import fields, replace
from typing import Generator

from pyconlang.config import Config, config
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


@contextmanager
def config_as(new_config: Config) -> Generator[None, None, None]:
    original_config = replace(config())
    update_config(new_config)
    yield
    update_config(original_config)


def update_config(new_config: Config) -> None:
    for field in fields(Config):
        setattr(config(), field.name, getattr(new_config, field.name))
