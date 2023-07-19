from collections.abc import Iterable

# from string import whitespace
from typing import TypeVar

from .domain import (
    Component,
    Compound,
    Compoundable,
    DefaultSentence,
    DefaultWord,
    Definable,
    Fusible,
    Fusion,
    Joiner,
    JoinerStress,
    Lexeme,
    Morpheme,
    Prefix,
    Rule,
    Scope,
    ScopedLexeme,
    Sentence,
    Suffix,
    Tag,
    Tags,
    Word,
)
from .pyrsec import Parser, default, fix, lift2, lift3, regex, string, token

T = TypeVar("T")


def parse_sentence(string: str) -> DefaultSentence:
    return sentence.parse_or_raise(string)  # todo: parse all?


def parse_definables(string: str) -> Sentence[Definable]:
    return definable_sentence.parse_or_raise(string)


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


ident = regex(r"[A-Za-z0-9-]+")

default_scope = string("%%")[lambda _: None]
root_scope = string("%")[lambda _: Scope()]
actual_scope = (string("%") >> ident)[Scope]
non_default_scope = actual_scope ^ root_scope
scope = default_scope ^ non_default_scope
opt_scope = -scope

lexeme = (string("<") >> regex(r"[^<>]+") << string(">"))[Lexeme]
scoped_lexeme = (lexeme & opt_scope)[lift2(ScopedLexeme)]

rule = (string("@") >> ident)[Rule]

unicode_word = regex(r'[^\s.@"]+')

morpheme = (string("*") >> unicode_word & -rule)[lift2(Morpheme)]

base_unit = scoped_lexeme ^ morpheme

prefix = (ident << string("."))[Prefix]
suffix = (string(".") >> ident)[Suffix]
affix = prefix ^ suffix


def fusion(stem: Parser[str, Fusible]) -> Parser[str, Fusion[Fusible]]:
    return (~prefix & stem & ~suffix)[lift3(Fusion[Fusible].from_prefixes_and_suffixes)]


default_fusion = fusion(base_unit)
lexeme_fusion = fusion(lexeme)

head_stress = string("!+")[lambda _: JoinerStress.HEAD]
tail_stress = string("+!")[lambda _: JoinerStress.TAIL]
stress = head_stress ^ tail_stress
joiner = (stress & -rule)[lift2(Joiner)]


def word(compoundable: Parser[str, Compoundable]) -> Parser[str, Word[Compoundable]]:
    def word_parser(
        parser: Parser[str, Word[Compoundable]]
    ) -> Parser[str, Word[Compoundable]]:
        bracketed_word = string('"') >> parser << string('"')
        component = compoundable[Component[Compoundable]]
        component_or_bracketed = bracketed_word ^ component
        joined = (component_or_bracketed & token(joiner) & component_or_bracketed)[
            lift3(Compound[Compoundable])
        ]
        return joined ^ component_or_bracketed

    return fix(word_parser)


default_word = word(default_fusion)

words = ~token(default_word)

tag_key = ident[Tag]
tag_key_value = (ident & string(":") >> ident)[lift2(Tag)]
tag = tag_key_value ^ tag_key
just_tags = (string("{") >> ~token(tag) << string("}"))[set[Tag]]
opt_just_tags = (-just_tags)[default(set)]
tags = (opt_just_tags & token(opt_scope))[lift2(Tags.from_set_and_scope)]
opt_tags = (-tags)[default(Tags)]

sentence = (opt_tags & words)[lift2(Sentence[DefaultWord])]

definable = lexeme ^ affix
definables = ~token(definable)

definable_sentence = (opt_tags & definables)[lift2(Sentence[Definable])]
