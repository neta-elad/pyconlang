from pathlib import Path
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
    Entry,
    Form,
    Fusion,
    PartOfSpeech,
    Proto,
    Rule,
    Template,
    TemplateName,
    Var,
)
from . import Lexicon

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


def make_diagrams() -> None:
    lexicon.create_diagram("diagrams.html", show_results_names=True)


def parse_lexicon(string: str) -> Lexicon:
    result = lexicon.parse_string(string, parse_all=True)[0]

    if not isinstance(result, Lexicon):
        raise RuntimeError(f"Could not parse {string}")

    return result


def parse_lexicon_file(filename: Path = Path("lexicon.txt")) -> Lexicon:
    return parse_lexicon(filename.read_text())


def parse_sentence(string: str) -> List[Form]:
    return cast(List[Form], list(sentence.parse_string(string, parse_all=True)))


ident = Word(alphanums + "-").set_name("ident")
rule = (Suppress("@") + ident).set_parse_action(token_map(Rule)).set_name("rule")
canonical = (
    (Suppress("<") + Word(alphanums + "-" + " ") + Suppress(">"))
    .set_parse_action(token_map(Canonical))
    .set_name("canonical")
)
unicode_word = Word(pyparsing_unicode.BasicMultilingualPlane.alphas).set_name(
    "unicode_word"
)
proto = (
    (Suppress("*") + unicode_word + explicit_opt(rule))
    .set_parse_action(tokens_map(Proto))
    .set_name("proto")
)
template_name = (
    (Suppress("&") + ident)
    .set_parse_action(token_map(TemplateName))
    .set_name("template_name")
)
part_of_speech = (
    (Suppress("(") + Word(alphas) + Suppress(".)"))
    .set_parse_action(token_map(PartOfSpeech))
    .set_name("part_of_speech")
)
rest = rest_of_line.set_parse_action(token_map(str.strip)).set_name("rest")
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
var = (
    (prefix[...] + Suppress("$") + suffix[...])
    .set_parse_action(Var.from_iterable)
    .set_name("var")
)
template = (
    (Suppress("template") + template_name + var[1, ...])
    .set_parse_action(tokens_map(Template.from_args))
    .set_name("template")
)
fusion = (
    (Group(prefix[...], True) + canonical + Group(suffix[...], True))
    .set_parse_action(tokens_map(Fusion.from_prefixes_and_suffixes))
    .set_name("fusion")
)
form = (proto | fusion).set_name("form")
lexical_sources = (
    Suppress("(") + canonical[1, ...].set_parse_action(tuple) + Suppress(")")
)
affix_definition = (
    (
        Suppress("affix")
        + Opt("!")
        .set_parse_action(lambda tokens: len(tokens) > 0)
        .set_results_name("stressed")
        + affix
        + explicit_opt(rule)
        + explicit_opt(form)
        + explicit_opt(lexical_sources, ())
        + rest
    )
    .set_parse_action(tokens_map(AffixDefinition))
    .set_name("affix_definition")
)
entry = (
    (
        Suppress("entry")
        + explicit_opt(template_name)
        + canonical
        + form
        + part_of_speech
        + rest
    )
    .set_parse_action(tokens_map(Entry))
    .set_name("entry")
)
lexicon = (
    (entry | affix_definition | template)[...]
    .set_parse_action(Lexicon.from_iterable)
    .set_name("lexicon")
)

sentence = form[...]

if __name__ == "__main__":
    make_diagrams()
