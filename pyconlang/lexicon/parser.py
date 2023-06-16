from collections.abc import Iterable
from typing import cast

from pyparsing import (
    FollowedBy,
    Group,
    Opt,
    ParserElement,
    Regex,
    Suppress,
    Word,
    alphas,
    token_map,
)

from ..parser import (
    affix,
    compound,
    explicit_opt,
    ident,
    lexeme,
    prefix,
    rule,
    suffix,
    tokens_map,
)
from ..types import AffixDefinition, Entry, PartOfSpeech, Template, TemplateName, Var


def make_diagrams() -> None:
    lexicon.create_diagram("diagrams.html", show_results_names=True)


def parse_lexicon(
    lines: Iterable[str],
) -> Iterable[Entry | AffixDefinition | Template]:
    return [
        cast(Entry | AffixDefinition | Template, parsed_record[0])
        for line in lines
        if (parsed_record := lexicon_line.parse_string(line, parse_all=True))
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
    (Suppress("template") - template_name - var[1, ...])
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
        - lexeme
        - compound
        - part_of_speech
        - rest
    )
    .set_parse_action(tokens_map(Entry))
    .set_name("entry")
)

record = (entry ^ affix_definition ^ template).set_name("record")

comment = Suppress(Regex(r"#(?:\\\n|[^\n])*")).set_name("comment")

lexicon_line = (Opt(record) + Opt(comment)).set_name("lexicon line")

lexicon = ((lexicon_line + Suppress("\n"))[...]).set_name(  # - Opt(Suppress("\n"))
    "lexicon"
)


if __name__ == "__main__":
    make_diagrams()
