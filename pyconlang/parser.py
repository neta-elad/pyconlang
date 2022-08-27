from string import whitespace
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

from pyconlang.types import Affix, AffixType, Fusion, Lexeme, Morpheme, Rule

T = TypeVar("T")


def tokens_map(fun: Callable[..., T]) -> Callable[[ParseResults], T]:
    def action(tokens: ParseResults) -> T:
        return fun(*tokens)

    return action


def parse_sentence(string: str) -> List[Fusion]:
    return cast(List[Fusion], list(sentence.parse_string(string, parse_all=True)))


ParserElement.set_default_whitespace_chars(" \t")

lexeme = (
    (Suppress("<") - Word(alphanums + "-" + " ") - Suppress(">"))
    .set_parse_action(token_map(Lexeme))
    .set_name("lexeme")
)

ident = Word(alphanums + "-").set_name("ident")

rule = (Suppress("@") - ident).set_parse_action(token_map(Rule)).set_name("rule")

unicode_word = Word(
    pyparsing_unicode.BasicMultilingualPlane.printables,
    exclude_chars=whitespace + ".@",
).set_name("unicode_word")
morpheme = (
    (Suppress("*") - unicode_word - Opt(rule))
    .set_parse_action(tokens_map(Morpheme))
    .set_name("morpheme")
)

base_unit = (lexeme ^ morpheme).set_name("simple_form")

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

fusion = (
    (
        (Group(prefix[...], True) + FollowedBy(base_unit))
        - base_unit
        - Group(suffix[...], True)
    )
    .set_parse_action(tokens_map(Fusion.from_prefixes_and_suffixes))
    .set_name("fusion")
)

sentence = fusion[...]
