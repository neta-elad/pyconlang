from string import digits, punctuation, whitespace
from typing import Callable, List, TypeVar, cast

from pyparsing import (
    FollowedBy,
    Group,
    Opt,
    ParserElement,
    ParseResults,
    Suppress,
    Word,
    alphanums,
    pyparsing_unicode,
    token_map,
)

from pyconlang.types import Affix, AffixType, Canonical, Compound, Proto, Rule

T = TypeVar("T")


def tokens_map(fun: Callable[..., T]) -> Callable[[ParseResults], T]:
    def action(tokens: ParseResults) -> T:
        return fun(*tokens)

    return action


def parse_sentence(string: str) -> List[Compound]:
    return cast(List[Compound], list(sentence.parse_string(string, parse_all=True)))


ParserElement.set_default_whitespace_chars(" \t")

ident = Word(alphanums + "-").set_name("ident")
rule = (Suppress("@") - ident).set_parse_action(token_map(Rule)).set_name("rule")
canonical = (
    (Suppress("<") - Word(alphanums + "-" + " ") - Suppress(">"))
    .set_parse_action(token_map(Canonical))
    .set_name("canonical")
)
unicode_word = Word(
    pyparsing_unicode.BasicMultilingualPlane.printables,
    exclude_chars=whitespace + digits + punctuation,
).set_name("unicode_word")
proto = (
    (Suppress("*") - unicode_word - Opt(rule))
    .set_parse_action(tokens_map(Proto))
    .set_name("proto")
)
simple_form = (canonical ^ proto).set_name("simple_form")
prefix = (
    (ident - Suppress("."))
    .set_parse_action(token_map(Affix, AffixType.PREFIX))
    .set_name("prefix")
)
suffix = (
    (Suppress(".") - ident)
    .set_parse_action(token_map(Affix, AffixType.SUFFIX))
    .set_name("suffix")
)
compound = (
    (
        (Group(prefix[...], True) + FollowedBy(simple_form))
        - simple_form
        - Group(suffix[...], True)
    )
    .set_parse_action(tokens_map(Compound.from_prefixes_and_suffixes))
    .set_name("compound")
)
sentence = compound[...]
