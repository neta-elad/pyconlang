from string import digits, punctuation, whitespace
from typing import Any, Callable, List, TypeVar, Union, cast

from pyparsing import (
    Group,
    Opt,
    ParserElement,
    ParseResults,
    Suppress,
    Word,
    alphanums,
    alphas,
    pyparsing_unicode,
    rest_of_line,
    token_map,
)

from ..types import (
    Affix,
    AffixDefinition,
    AffixType,
    Canonical,
    Compound,
    Entry,
    PartOfSpeech,
    Proto,
    Rule,
    Template,
    TemplateName,
    Var,
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


def parse_sentence(string: str) -> List[Compound]:
    return cast(List[Compound], list(sentence.parse_string(string, parse_all=True)))


def make_diagrams() -> None:
    lexicon.create_diagram("diagrams.html", show_results_names=True)


ident = Word(alphanums + "-").set_name("ident")

rule = (Suppress("@") + ident).set_parse_action(token_map(Rule)).set_name("rule")

canonical = (
    (Suppress("<") + Word(alphanums + "-" + " ") + Suppress(">"))
    .set_parse_action(token_map(Canonical))
    .set_name("canonical")
)

unicode_word = Word(
    pyparsing_unicode.BasicMultilingualPlane.printables,
    exclude_chars=whitespace + digits + punctuation,
).set_name("unicode_word")

proto = (
    (Suppress("*") + unicode_word + Opt(rule))
    .set_parse_action(tokens_map(Proto))
    .set_name("proto")
)

simple_form = (canonical | proto).set_name('simple_form')

prefix = (
    (ident + Suppress("."))
    .set_parse_action(token_map(Affix, AffixType.PREFIX))
    .set_name("prefix")
)
suffix = (
    (Suppress(".") + ident)
    .set_parse_action(token_map(Affix, AffixType.SUFFIX))
    .set_name("suffix")
)
affix = (prefix | suffix).set_name("affix")

compound = (
    (Group(prefix[...], True) + simple_form + Group(suffix[...], True))
    .set_parse_action(tokens_map(Compound.from_prefixes_and_suffixes))
    .set_name("compound")
)

var = (
    (prefix[...] + Suppress("$") + suffix[...])
    .set_parse_action(Var.from_iterable)
    .set_name("var")
)

template_name = (
    (Suppress("&") + ident)
    .set_parse_action(token_map(TemplateName))
    .set_name("template_name")
)
template = (
    (Suppress("template") + template_name + var[1, ...])
    .set_parse_action(tokens_map(Template.from_args))
    .set_name("template")
)

lexical_sources = (
    Suppress("(") + canonical[1, ...].set_parse_action(tuple) + Suppress(")")
)

rest = rest_of_line.set_parse_action(token_map(str.strip)).set_name("rest")

affix_definition = (
    (
        Suppress("affix")
        + Opt("!")
        .set_parse_action(lambda tokens: len(tokens) > 0)
        .set_results_name("stressed")
        + affix
        + explicit_opt(rule)
        + explicit_opt(simple_form)
        + explicit_opt(lexical_sources, ())
        + rest
    )
    .set_parse_action(tokens_map(AffixDefinition))
    .set_name("affix_definition")
)

part_of_speech = (
    (Suppress("(") + Word(alphas) + Suppress(".)"))
    .set_parse_action(token_map(PartOfSpeech))
    .set_name("part_of_speech")
)

entry = (
    (
        Suppress("entry")
        + explicit_opt(template_name)
        + canonical
        + compound
        + part_of_speech
        + rest
    )
    .set_parse_action(tokens_map(Entry))
    .set_name("entry")
)

lexicon = (entry | affix_definition | template)[...].set_name("lexicon")

sentence = compound[...]

if __name__ == "__main__":
    make_diagrams()
