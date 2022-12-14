from pyparsing import (
    FollowedBy,
    Opt,
    ParserElement,
    Regex,
    Suppress,
    Word,
    alphas,
    token_map,
)

from ..parser import (
    base_unit,
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


ParserElement.set_default_whitespace_chars(" \t")


var = (
    ((prefix[...] + FollowedBy("$")) - Suppress("$") - suffix[...])
    .set_parse_action(Var.from_iterable)
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

affix = (prefix ^ suffix).set_name("affix")
affix_definition = (
    (
        Suppress("affix")
        - Opt("!")
        .set_parse_action(lambda tokens: len(tokens) > 0)
        .set_results_name("stressed")
        - affix
        - explicit_opt(rule)
        - explicit_opt(base_unit)
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

lexicon = (
    (Opt(record) + Opt(comment) + Suppress("\n"))[...]  # - Opt(Suppress("\n"))
).set_name("lexicon")

if __name__ == "__main__":
    make_diagrams()
