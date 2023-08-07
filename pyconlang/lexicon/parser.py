from collections.abc import Iterable
from pathlib import Path
from typing import Literal, cast

from pyrsercomb import (
    default,
    eof,
    eol,
    lift2,
    lift3,
    lift6,
    lift7,
    regex,
    string,
    token,
    whitespace,
)

from ..domain import Lexeme, PartOfSpeech, Scoped
from ..parser import (
    affix,
    default_word,
    ident,
    lexeme,
    lexeme_fusion,
    non_default_scope,
    opt_scope,
    opt_tags,
    rule,
    scoped_prefix,
    scoped_suffix,
)
from .domain import (
    AffixDefinition,
    Entry,
    ScopeDefinition,
    Template,
    TemplateName,
    VarFusion,
)


def parse_lexicon(
    lines: Iterable[str],
) -> Iterable[Entry | AffixDefinition | Template | ScopeDefinition | Path]:
    return [
        parsed_line
        for line in lines
        if (parsed_line := lexicon_line.parse_or_raise(line))
    ]


var_symbol = string("$")[lambda _: cast(Literal["$"], "$")]
var = (~scoped_prefix & var_symbol & ~scoped_suffix)[
    lift3(VarFusion.from_prefixes_and_suffixes)
]
template_name = (string("&") >> ident)[TemplateName]

template = (
    string("template") >> token(template_name)
    & opt_tags
    & (~token(var))[tuple[VarFusion]]
)[lift3(Template)]

rest_of_line = regex(r"[^#\n]*")[str.strip]

lexical_sources = string("(") >> (~token(lexeme))[tuple[Lexeme]] << string(")")

entry_form = (token(opt_scope) & token(default_word))[
    lambda pair: Scoped(pair[1], pair[0])
]

affix_form = entry_form ^ var

affix_definition = (
    (
        string("affix") >> token(-string("!"))[bool]
        & opt_tags
        & token(affix)
        & token(-rule)
        & token(-affix_form)
        & token(-lexical_sources)[default(tuple[Lexeme])]
        & rest_of_line
    )
)[lift7(AffixDefinition)]

part_of_speech = (string("(") >> regex(r"[A-Za-z]+") << string(".)"))[PartOfSpeech]

entry = (
    string("entry") >> -token(template_name)
    & opt_tags
    & token(lexeme_fusion)
    & token(entry_form)
    & token(part_of_speech)
    & rest_of_line
)[lift6(Entry)]

double_quoted_string = string('"') >> regex(r'[^"]+') << string('"')
single_quoted_string = string("'") >> regex(r"[^']+") << string("'")
quoted_string = double_quoted_string ^ single_quoted_string

path = quoted_string[Path]

base_scope_definition = string("scope") >> token(non_default_scope) << string(
    ":"
) & token(non_default_scope)

scope_definition_without_path = base_scope_definition[lift2(ScopeDefinition)]

scope_definition_with_path = (base_scope_definition & token(path))[
    lift3(ScopeDefinition)
]

scope_definition = scope_definition_with_path ^ scope_definition_without_path

record = entry | affix_definition | template | scope_definition

include = string("include") >> token(path)

meaningful_segment = record | include

comment = regex(r"\s*#.*")

lexicon_line = (
    (meaningful_segment | whitespace()[lambda _: None]) << -comment << (eol() ^ eof())
)
