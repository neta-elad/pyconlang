from inspect import cleandoc
from pathlib import Path

from pyconlang.domain import (
    AffixDefinition,
    Component,
    Compound,
    Entry,
    Fusion,
    Joiner,
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
from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.parser import (
    affix_definition,
    comment,
    entry,
    include,
    lexical_sources,
    part_of_speech,
    quoted_string,
    template_name,
    var,
)
from pyconlang.parser import affix

from ..test_parser import parse


def test_entry_parts() -> None:
    assert parse(template_name, "&template") == TemplateName("template")
    assert parse(part_of_speech, "(adj.)") == PartOfSpeech("adj")


def test_entry() -> None:
    assert parse(entry, "entry <strong> *kipu@era1 (adj.) strong, stable") == Entry(
        None,
        Lexeme("strong"),
        Component(Fusion(Morpheme("kipu", Rule("era1")))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> *kipu@era1.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Lexeme("strong"),
        Component(Fusion(Morpheme("kipu", Rule("era1")), (), (Suffix("PL"),))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> <heavy>.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Lexeme("strong"),
        Component(Fusion(Lexeme("heavy"), (), (Suffix("PL"),))),
        PartOfSpeech("adj"),
        "strong, stable",
    )


def test_affix() -> None:
    assert parse(affix, ".PL") == Suffix("PL")
    assert parse(affix, "PL.") == Prefix("PL")


def test_affix_definition() -> None:
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
        Component(Fusion(Morpheme("proto"))),
        (Lexeme("big"), Lexeme("pile")),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL *proto@era plural for inanimate"
    ) == AffixDefinition(
        False,
        Suffix("PL"),
        None,
        Component(Fusion(Morpheme("proto", Rule("era")))),
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
        Component(Fusion(Lexeme("big"), (), (Suffix("PL"),))),
        (),
        description="collective form",
    )

    assert parse(
        affix_definition, 'affix COL. "<big> !+ <pile>.PL" collective form'
    ) == AffixDefinition(
        False,
        Prefix("COL"),
        None,
        Compound(
            Component(Fusion(Lexeme("big"))),
            Joiner.head(),
            Component(Fusion(Lexeme("pile"), (), (Suffix("PL"),))),
        ),
        (),
        description="collective form",
    )


def test_comment() -> None:
    assert not comment.parse_string("# <nothing at all *..", parse_all=True)
    assert not comment.parse_string("   ### <nothing at all *..", parse_all=True)


def test_lexicon(parsed_lexicon: Lexicon) -> None:
    assert isinstance(parsed_lexicon, Lexicon)

    assert parsed_lexicon.entries == {
        Entry(
            None,
            Lexeme("strong"),
            Component(Fusion(Morpheme("kipu", Rule("era1")))),
            PartOfSpeech("adj"),
            "strong, stable",
        ),
        Entry(
            None,
            Lexeme("big"),
            Component(Fusion(Morpheme("iki"))),
            PartOfSpeech("adj"),
            "big, great",
        ),
        Entry(
            TemplateName("plural"),
            Lexeme("stone"),
            Component(Fusion(Morpheme("apak"))),
            PartOfSpeech("n"),
            "stone, pebble",
        ),
        Entry(
            None,
            Lexeme("gravel"),
            Component(Fusion(Lexeme("stone"), (), (Suffix("PL"),))),
            PartOfSpeech("n"),
            "gravel",
        ),
        Entry(
            None,
            Lexeme("pile"),
            Component(Fusion(Morpheme("ma"))),
            PartOfSpeech("n"),
            "pile",
        ),
    }

    assert parsed_lexicon.affixes == {
        AffixDefinition(
            stressed=False,
            affix=Suffix("PL"),
            era=None,
            form=Component(Fusion(Morpheme("iki", Rule("era1")))),
            sources=(Lexeme("big"), Lexeme("pile")),
            description="plural for inanimate",
        ),
        AffixDefinition(
            stressed=False,
            affix=Suffix("COL"),
            era=None,
            form=Component(Fusion(Morpheme(form="ma", era=None))),
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
            form=Component(
                Fusion(
                    stem=Lexeme(name="stone"),
                    prefixes=(),
                    suffixes=(Suffix("COL"),),
                )
            ),
            sources=(),
            description="made of stone",
        ),
        AffixDefinition(
            stressed=False,
            affix=Suffix("DIST-PL"),
            era=None,
            form=None,
            sources=(Lexeme("big"), Lexeme("pile")),
            description="distributive plural",
        ),
    }

    assert parsed_lexicon.templates == {
        Template(
            TemplateName("plural"),
            (Var((), ()), Var((), (Suffix("PL"),))),
        )
    }


def test_var() -> None:
    assert parse(var, "$") == Var((), ())
    assert parse(var, "$.PL") == Var((), (Suffix("PL"),))
    assert parse(var, "DEF.$.PL.COL") == Var(
        (Prefix("DEF"),),
        (
            Suffix("PL"),
            Suffix("COL"),
        ),
    )


def test_include() -> None:
    assert parse(quoted_string, '"hello"') == "hello"
    assert parse(quoted_string, "'world'") == "world"

    assert parse(include, "include 'a/relative/path'") == Path("a/relative/path")
    assert parse(include, "include '/an/relative/path'") == Path("/an/relative/path")


def test_include_mechanism(
    tmpdir: Path, sample_lexicon: str, parsed_lexicon: Lexicon
) -> None:
    main = tmpdir / "main.pycl"
    subdir = tmpdir / "subdir"
    subdir.mkdir(parents=True, exist_ok=True)
    intermediate = subdir / "inter.pycl"
    included = subdir / "included.pycl"

    main.write_text(
        cleandoc(
            """
    include "subdir/inter.pycl"
    """
        )
    )

    intermediate.write_text(
        cleandoc(
            """
    include "./included.pycl"
    """
        )
    )

    included.write_text(sample_lexicon)

    lexicon = Lexicon.from_path(main)

    assert len(lexicon.entries) == len(parsed_lexicon.entries)
    assert len(lexicon.affixes) == len(parsed_lexicon.affixes)
    assert len(lexicon.templates) == len(parsed_lexicon.templates)
