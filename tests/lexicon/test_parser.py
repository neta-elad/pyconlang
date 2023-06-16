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
    AffixDefinition,
    Compound,
    CompoundStress,
    Entry,
    Fusion,
    Lexeme,
    Morpheme,
    PartOfSpeech,
    Prefix,
    Rule,
    Suffix,
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
        Fusion(Morpheme("kipu", Rule("era1")), (), (Suffix("PL"),)),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> <heavy>.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Lexeme("strong"),
        Fusion(Lexeme("heavy"), (), (Suffix("PL"),)),
        PartOfSpeech("adj"),
        "strong, stable",
    )


def test_affix():
    assert parse(affix, ".PL") == Suffix("PL")
    assert parse(affix, "PL.") == Prefix("PL")


def test_affix_definition():
    assert parse(lexical_sources, "(<big> <pile>)") == (
        Lexeme("big"),
        Lexeme("pile"),
    )

    assert parse(
        affix_definition, "affix ! .PL @era *proto (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        True,
        Suffix("PL"),
        Rule("era"),
        Fusion(Morpheme("proto")),
        (Lexeme("big"), Lexeme("pile")),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL *proto@era plural for inanimate"
    ) == AffixDefinition(
        False,
        Suffix("PL"),
        None,
        Fusion(Morpheme("proto", Rule("era"))),
        (),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        False,
        Suffix("PL"),
        None,
        None,
        (Lexeme("big"), Lexeme("pile")),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix COL. <big>.PL collective form"
    ) == AffixDefinition(
        False,
        Prefix("COL"),
        None,
        Fusion(Lexeme("big"), (), (Suffix("PL"),)),
        (),
        description="collective form",
    )

    assert parse(
        affix_definition, "affix COL. [<big> !+ <pile>.PL] collective form"
    ) == AffixDefinition(
        False,
        Prefix("COL"),
        None,
        Compound(
            Fusion(Lexeme("big")),
            CompoundStress.HEAD,
            None,
            Fusion(Lexeme("pile"), (), (Suffix("PL"),)),
        ),
        (),
        description="collective form",
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
                Fusion(Lexeme("stone"), (), (Suffix("PL"),)),
                PartOfSpeech("n"),
                "gravel",
            ),
        }
    )

    assert frozenset(parsed_lexicon.affixes) == frozenset(
        {
            AffixDefinition(
                stressed=False,
                affix=Suffix("PL"),
                era=None,
                form=Fusion(Morpheme("iki", Rule("era1"))),
                sources=(Lexeme("big"), Lexeme("pile")),
                description="plural for inanimate",
            ),
            AffixDefinition(
                stressed=False,
                affix=Suffix("COL"),
                era=None,
                form=Fusion(Morpheme(form="ma", era=None)),
                sources=(),
                description="collective",
            ),
            AffixDefinition(
                stressed=False,
                affix=Suffix("LARGE"),
                era=None,
                form=Var(
                    prefixes=(),
                    suffixes=(
                        Suffix("COL"),
                        Suffix("PL"),
                    ),
                ),
                sources=(),
                description="large plural",
            ),
            AffixDefinition(
                stressed=False,
                affix=Prefix("STONE"),
                era=None,
                form=Fusion(
                    stem=Lexeme(name="stone"),
                    prefixes=(),
                    suffixes=(Suffix("COL"),),
                ),
                sources=(),
                description="made of stone",
            ),
        }
    )

    assert frozenset(parsed_lexicon.templates) == frozenset(
        {
            Template(
                TemplateName("plural"),
                (Var((), ()), Var((), (Suffix("PL"),))),
            )
        }
    )


def test_var(sample_lexicon):
    assert parse(var, "$") == Var((), ())
    assert parse(var, "$.PL") == Var((), (Suffix("PL"),))
    assert parse(var, "DEF.$.PL.COL") == Var(
        (Prefix("DEF"),),
        (
            Suffix("PL"),
            Suffix("COL"),
        ),
    )
