from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.parser import (
    affix,
    affix_definition,
    comment,
    entry,
    lexical_sources,
    part_of_speech,
    template_name,
    var,
)
from pyconlang.types import (
    Affix,
    AffixDefinition,
    AffixType,
    Entry,
    Fusion,
    Lexeme,
    Morpheme,
    PartOfSpeech,
    Rule,
    Template,
    TemplateName,
    Var,
)

from ..test_parser import parse


def test_entry_parts():
    assert parse(template_name, "&template") == TemplateName("template")
    assert parse(part_of_speech, "(adj.)") == PartOfSpeech("adj")


def test_entry():
    assert parse(entry, "entry <strong> *kipu@era1 (adj.) strong, stable") == Entry(
        None,
        Lexeme("strong"),
        Fusion(Morpheme("kipu", Rule("era1"))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> *kipu@era1.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Lexeme("strong"),
        Fusion(Morpheme("kipu", Rule("era1")), (Affix("PL", AffixType.SUFFIX),)),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> <heavy>.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Lexeme("strong"),
        Fusion(Lexeme("heavy"), (Affix("PL", AffixType.SUFFIX),)),
        PartOfSpeech("adj"),
        "strong, stable",
    )


def test_affix():
    assert parse(affix, ".PL") == Affix("PL", AffixType.SUFFIX)
    assert parse(affix, "PL.") == Affix("PL", AffixType.PREFIX)


def test_affix_definition():
    assert parse(lexical_sources, "(<big> <pile>)") == (
        Lexeme("big"),
        Lexeme("pile"),
    )

    assert parse(
        affix_definition, "affix ! .PL @era *proto (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        True,
        Affix("PL", AffixType.SUFFIX),
        Rule("era"),
        Morpheme("proto"),
        (Lexeme("big"), Lexeme("pile")),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL *proto@era plural for inanimate"
    ) == AffixDefinition(
        False,
        Affix("PL", AffixType.SUFFIX),
        None,
        Morpheme("proto", Rule("era")),
        (),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        False,
        Affix("PL", AffixType.SUFFIX),
        None,
        None,
        (Lexeme("big"), Lexeme("pile")),
        "plural for inanimate",
    )


def test_comment():
    assert not comment.parse_string("# <nothing at all *..", parse_all=True)
    assert not comment.parse_string("   ### <nothing at all *..", parse_all=True)


def test_lexicon(parsed_lexicon):
    assert isinstance(parsed_lexicon, Lexicon)

    assert frozenset(parsed_lexicon.entries) == frozenset(
        {
            Entry(
                None,
                Lexeme("strong"),
                Fusion(Morpheme("kipu", Rule("era1"))),
                PartOfSpeech("adj"),
                "strong, stable",
            ),
            Entry(
                None,
                Lexeme("big"),
                Fusion(Morpheme("iki")),
                PartOfSpeech("adj"),
                "big, great",
            ),
            Entry(
                TemplateName("plural"),
                Lexeme("stone"),
                Fusion(Morpheme("apak")),
                PartOfSpeech("n"),
                "stone, pebble",
            ),
            Entry(
                None,
                Lexeme("gravel"),
                Fusion(Lexeme("stone"), (Affix("PL", AffixType.SUFFIX),)),
                PartOfSpeech("n"),
                "gravel",
            ),
        }
    )

    assert frozenset(parsed_lexicon.affixes) == frozenset(
        {
            AffixDefinition(
                False,
                Affix("PL", AffixType.SUFFIX),
                None,
                Morpheme("iki", Rule("era1")),
                (Lexeme("big"), Lexeme("pile")),
                "plural for inanimate",
            )
        }
    )

    assert frozenset(parsed_lexicon.templates) == frozenset(
        {
            Template(
                TemplateName("plural"), (Var(()), Var((Affix("PL", AffixType.SUFFIX),)))
            )
        }
    )


def test_var(sample_lexicon):
    assert parse(var, "$") == Var(())
    assert parse(var, "$.PL") == Var((Affix("PL", AffixType.SUFFIX),))
    assert parse(var, "DEF.$.PL.COL") == Var(
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("COL", AffixType.SUFFIX),
        )
    )
