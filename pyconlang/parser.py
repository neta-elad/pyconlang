from string import whitespace
from typing import Any, Callable, List, TypeVar, Union, cast

from pyparsing import (
    FollowedBy,
    Forward,
    Group,
    Literal,
    Opt,
    ParserElement,
    ParseResults,
    Suppress,
    Word,
    alphanums,
    pyparsing_unicode,
    token_map,
)

from .types import (
    Affix,
    AffixType,
    Compound,
    CompoundStress,
    Fusion,
    Lexeme,
    Morpheme,
    Rule,
)

T = TypeVar("T")


def explicit_opt(expr: Union[ParserElement, str], value: Any = None) -> ParserElement:
    def first_or(tokens: ParseResults) -> Any:
        return tokens or [value]

    optional = Opt(expr).set_parse_action(first_or)
    optional.mayReturnEmpty = False
    return optional


def tokens_map(fun: Callable[..., T]) -> Callable[[ParseResults], T]:
    def action(tokens: ParseResults) -> T:
        return fun(*tokens)

    return action


def const_action(value: T) -> Callable[[], T]:
    def action() -> T:
        return value

    return action


def parse_sentence(string: str) -> List[Compound]:
    return cast(List[Compound], list(sentence.parse_string(string, parse_all=True)))


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
    exclude_chars=whitespace + ".@[]",
).set_name("unicode_word")
morpheme = (
    (Suppress("*") - unicode_word - Opt(rule))
    .set_parse_action(tokens_map(Morpheme))
    .set_name("morpheme")
)

base_unit = (lexeme ^ morpheme).set_name("base unit")

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

head_stresser = Literal("!+").set_parse_action(const_action(CompoundStress.HEAD))
tail_stresser = Literal("+!").set_parse_action(const_action(CompoundStress.TAIL))

joiner = (
    (head_stresser ^ tail_stresser) - explicit_opt(rule).set_name("maybe rule")
).set_name("joiner")

compound = Forward()
compound.set_name("compound")

bracketed_compound = (Suppress("[") - compound - Suppress("]")).set_name(
    "bracketed compound"
)

fusion_or_bracketed = (fusion ^ bracketed_compound).set_name("fusion or bracketed")

joined_compound = (
    Group((fusion_or_bracketed + FollowedBy(joiner)) - joiner - fusion_or_bracketed)
    .set_parse_action(token_map(tokens_map(Compound)))
    .set_name("joined compound")
)


compound <<= fusion_or_bracketed ^ joined_compound


sentence = compound[...]
