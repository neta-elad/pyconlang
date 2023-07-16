from collections.abc import Callable, Iterable
from string import whitespace
from typing import Any, TypeVar, cast

from pyparsing import (
    FollowedBy,
    Forward,
    Group,
    Literal,
    Opt,
    ParserElement,
    ParseResults,
    Suppress,
)
from pyparsing import Word as ParseWord
from pyparsing import alphanums, pyparsing_unicode, token_map

from .domain import (
    Component,
    Compound,
    Definable,
    Fusion,
    Joiner,
    JoinerStress,
    Lang,
    Lexeme,
    Morpheme,
    Prefix,
    Rule,
    Sentence,
    Suffix,
    Word,
)

T = TypeVar("T")


def explicit_opt(expr: ParserElement | str, value: Any = None) -> ParserElement:
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


def parse_sentence(string: str) -> Sentence[Word[Fusion]]:
    return cast(
        Sentence[Word[Fusion]], sentence.parse_string(string, parse_all=True)[0]
    )


def parse_definables(string: str) -> Sentence[Definable]:
    return cast(
        Sentence[Definable], definable_sentence.parse_string(string, parse_all=True)[0]
    )


def continue_lines(lines: Iterable[str]) -> Iterable[str]:
    current_line = ""
    for line in lines:
        if len(line) > 0 and line[0].isspace():
            current_line += line
        else:
            if current_line:
                yield current_line
            current_line = line

    if current_line:
        yield current_line


ParserElement.set_default_whitespace_chars(" \t")

lexeme = (
    (
        Suppress("<")
        - ParseWord(
            pyparsing_unicode.BasicMultilingualPlane.printables + whitespace,
            exclude_chars="<>",
        )
        - Suppress(">")
    )
    .set_parse_action(token_map(Lexeme))
    .set_name("lexeme")
)

ident = ParseWord(alphanums + "-").set_name("ident")

rule = (Suppress("@") - ident).set_parse_action(token_map(Rule)).set_name("rule")

unicode_word = ParseWord(
    pyparsing_unicode.BasicMultilingualPlane.printables,
    exclude_chars=whitespace + '.@"',
).set_name("unicode_word")
morpheme = (
    (Suppress("*") - unicode_word - Opt(rule))
    .set_parse_action(tokens_map(Morpheme))
    .set_name("morpheme")
)

base_unit = (lexeme ^ morpheme).set_name("base unit")

prefix = (ident - Suppress(".")).set_parse_action(token_map(Prefix)).set_name("prefix")
suffix = (Suppress(".") - ident).set_parse_action(token_map(Suffix)).set_name("suffix")

affix = (prefix ^ suffix).set_name("affix")

fusion = (
    (
        (Group(prefix[...], True) + FollowedBy(base_unit))
        - base_unit
        - Group(suffix[...], True)
    )
    .set_parse_action(tokens_map(Fusion.from_prefixes_and_suffixes))
    .set_name("fusion")
)

head_stresser = Literal("!+").set_parse_action(const_action(JoinerStress.HEAD))
tail_stresser = Literal("+!").set_parse_action(const_action(JoinerStress.TAIL))

joiner = (
    ((head_stresser ^ tail_stresser) - explicit_opt(rule).set_name("maybe rule"))
    .set_parse_action(tokens_map(Joiner))
    .set_name("joiner")
)

compound = Forward()
compound.set_name("compound")

bracketed_compound = (Suppress('"') - compound - Suppress('"')).set_name(
    "bracketed compound"
)

fusion_component = Group(fusion).set_parse_action(token_map(tokens_map(Component)))

fusion_or_bracketed = (fusion_component ^ bracketed_compound).set_name(
    "fusion or bracketed"
)

joined_compound = (
    Group((fusion_or_bracketed + FollowedBy(joiner)) - joiner - fusion_or_bracketed)
    .set_parse_action(token_map(tokens_map(Compound)))
    .set_name("joined compound")
)

compound <<= fusion_or_bracketed ^ joined_compound

words = Group(compound[...]).set_parse_action(token_map(list))
lang = (Suppress("%") - ident).set_parse_action(token_map(Lang))
opt_lang = explicit_opt(lang, Lang())

sentence = (opt_lang - words).set_parse_action(tokens_map(Sentence))

definable = (lexeme ^ affix).set_name("definable")

definables = Group(definable[...]).set_parse_action(token_map(list))

definable_sentence = (opt_lang - definables).set_parse_action(tokens_map(Sentence))
