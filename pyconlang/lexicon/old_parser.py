from collections.abc import Iterable
from pathlib import Path
from typing import cast

from pyparsing import (
    FollowedBy,
    Group,
    Opt,
    ParserElement,
    QuotedString,
    Regex,
    Suppress,
    Word,
    alphas,
    token_map,
)

from ..domain import PartOfSpeech
from ..old_parser import (
    affix,
    compound,
    explicit_opt,
    ident,
    lang,
    lexeme,
    lexeme_fusion,
    optional_tags,
    prefix,
    rule,
    suffix,
    tokens_map,
)
from .domain import AffixDefinition, Entry, LangDefinition, Template, TemplateName, Var


def make_diagrams() -> None:
    lexicon.create_diagram("diagrams.html", show_results_names=True)


def parse_lexicon(
    lines: Iterable[str],
) -> Iterable[Entry | AffixDefinition | Template | LangDefinition | Path]:
    return [
        cast(Entry | AffixDefinition | Template | LangDefinition | Path, parsed_line[0])
        for line in lines
        if (parsed_line := lexicon_line.parse_string(line, parse_all=True))
    ]


ParserElement.set_default_whitespace_chars(" \t")

var = (
    (
        (Group(prefix[...], True) + FollowedBy("$"))
        - Suppress("$")
        - Group(suffix[...], True)
    )
    .set_parse_action(tokens_map(Var.from_prefixes_and_suffixes))
    .set_name("var")
)
template_name = (
    (Suppress("&") - ident)
    .set_parse_action(token_map(TemplateName))
    .set_name("template_name")
)
template = (
    (Suppress("template") - template_name - optional_tags - var[1, ...])
    .set_parse_action(tokens_map(Template.from_args))
    .set_name("template")
)

rest_of_line = Regex(r"(?:\\\n|[^#\n])*").leave_whitespace().set_name("rest of line")

rest = rest_of_line.set_parse_action(token_map(str.strip)).set_name("rest")

lexical_sources = Suppress("(") - lexeme[1, ...].set_parse_action(tuple) - Suppress(")")

affix_form = (compound ^ var).set_name("affix form")

affix_definition = (
    (
        Suppress("affix")
        - Opt("!")
        .set_parse_action(lambda tokens: len(tokens) > 0)
        .set_results_name("stressed")
        - affix
        - optional_tags
        - explicit_opt(rule)
        - explicit_opt(affix_form)
        - explicit_opt(lexical_sources, ())
        - rest
    )
    .set_parse_action(tokens_map(AffixDefinition))
    .set_name("affix_definition")
)

part_of_speech = (
    (Suppress("(") - Word(alphas) - Suppress(".)"))
    .set_parse_action(token_map(PartOfSpeech))
    .set_name("part_of_speech")
)

entry = (
    (
        Suppress("entry")
        - explicit_opt(template_name)
        - optional_tags
        - lexeme_fusion
        - compound
        - part_of_speech
        - rest
    )
    .set_parse_action(tokens_map(Entry))
    .set_name("entry")
)


double_quoted_string = QuotedString(quote_char='"', esc_char="\\")
single_quoted_string = QuotedString(quote_char="'", esc_char="\\")
quoted_string = double_quoted_string ^ single_quoted_string

path = quoted_string.copy().set_parse_action(token_map(Path)).set_name("path")

lang_definition = (
    (Suppress("lang") - lang - Suppress(":") - lang - Opt(path))
    .set_parse_action(tokens_map(LangDefinition))
    .set_name("lang_definition")
)

record = (entry ^ affix_definition ^ template ^ lang_definition).set_name("record")

include = (
    (Suppress("include") - path)
    # .set_parse_action(token_map(Path))
    .set_name("include")
)

meaningful_segment = record ^ include

comment = Suppress(Regex(r"#(?:\\\n|[^\n])*")).set_name("comment")

lexicon_line = (Opt(meaningful_segment) + Opt(comment)).set_name("lexicon line")

lexicon = ((lexicon_line + Suppress("\n"))[...]).set_name(  # - Opt(Suppress("\n"))
    "lexicon"
)

if __name__ == "__main__":
    make_diagrams()
