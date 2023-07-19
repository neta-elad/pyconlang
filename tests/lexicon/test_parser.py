from inspect import cleandoc
from pathlib import Path

from pyconlang.domain import (
    Component,
    Compound,
    Fusion,
    Joiner,
    Lang,
    Lexeme,
    Morpheme,
    PartOfSpeech,
    Prefix,
    Rule,
    Suffix,
    Tag,
    Tags,
)
from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.domain import (
    AffixDefinition,
    Entry,
    LangDefinition,
    Template,
    TemplateName,
    Var,
)
from pyconlang.lexicon.parser import (
    affix_definition,
    comment,
    entry,
    include,
    lang_definition,
    lexical_sources,
    part_of_speech,
    quoted_string,
    template,
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
        Tags(),
        Fusion(Lexeme("strong")),
        Component(Fusion(Morpheme("kipu", Rule("era1")))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> *kipu@era1.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Tags(),
        Fusion(Lexeme("strong")),
        Component(Fusion(Morpheme("kipu", Rule("era1")), (), (Suffix("PL"),))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> <heavy>.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Tags(),
        Fusion(Lexeme("strong")),
        Component(Fusion(Lexeme("heavy").with_lang(), (), (Suffix("PL"),))),
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
        stressed=True,
        tags=Tags(),
        affix=Suffix("PL"),
        era=Rule("era"),
        form=Component(Fusion(Morpheme("proto"))),
        sources=(Lexeme("big"), Lexeme("pile")),
        description="plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL *proto@era plural for inanimate"
    ) == AffixDefinition(
        stressed=False,
        tags=Tags(),
        affix=Suffix("PL"),
        form=Component(Fusion(Morpheme("proto", Rule("era")))),
        description="plural for inanimate",
    )

    assert parse(
        affix_definition,
        "affix { foo bar:baz } .PL (<big> <pile>) plural for inanimate",
    ) == AffixDefinition(
        stressed=False,
        affix=Suffix("PL"),
        tags=Tags.from_set_and_lang({Tag("foo"), Tag("bar", "baz")}),
        era=None,
        form=None,
        sources=(Lexeme("big"), Lexeme("pile")),
        description="plural for inanimate",
    )

    assert parse(
        affix_definition, "affix COL. <big>.PL collective form"
    ) == AffixDefinition(
        stressed=False,
        tags=Tags(),
        affix=Prefix("COL"),
        era=None,
        form=Component(Fusion(Lexeme("big").with_lang(), (), (Suffix("PL"),))),
        sources=(),
        description="collective form",
    )

    assert parse(
        affix_definition, 'affix COL. "<big> !+ <pile>.PL" collective form'
    ) == AffixDefinition(
        stressed=False,
        tags=Tags(),
        affix=Prefix("COL"),
        era=None,
        form=Compound(
            Component(Fusion(Lexeme("big").with_lang())),
            Joiner.head(),
            Component(Fusion(Lexeme("pile").with_lang(), (), (Suffix("PL"),))),
        ),
        sources=(),
        description="collective form",
    )


def test_comment() -> None:
    assert parse(comment, "# <nothing at all *..") == "# <nothing at all *.."
    assert parse(comment, "   ### <nothing at all *..") == "   ### <nothing at all *.."


def test_lang_parent() -> None:
    assert parse(lang_definition, "lang %modern : %%") == LangDefinition(
        Lang("modern"), Lang()
    )

    assert parse(lang_definition, "lang %ultra-modern : %modern") == LangDefinition(
        Lang("ultra-modern"), Lang("modern")
    )

    assert parse(
        lang_definition, "lang %ultra-modern : %modern 'changes/ultra-modern.lsc'"
    ) == LangDefinition(
        Lang("ultra-modern"), Lang("modern"), Path("changes") / "ultra-modern.lsc"
    )


def test_lexicon(parsed_lexicon: Lexicon) -> None:
    assert isinstance(parsed_lexicon, Lexicon)

    assert parsed_lexicon.entries == {
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("strong")),
            Component(Fusion(Morpheme("kipu", Rule("era1")))),
            PartOfSpeech("adj"),
            "strong, stable",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("big")),
            Component(Fusion(Morpheme("iki"))),
            PartOfSpeech("adj"),
            "big, great",
        ),
        Entry(
            TemplateName("plural"),
            Tags(frozenset({Tag("lang")})),
            Fusion(Lexeme("stone")),
            Component(Fusion(Morpheme("apak"))),
            PartOfSpeech("n"),
            "stone, pebble",
        ),
        Entry(
            None,
            Tags(frozenset({Tag("lang", "modern")})),
            Fusion(Lexeme("stone")),
            Component(Fusion(Morpheme("kapa"))),
            PartOfSpeech("n"),
            "stone, pebble (modern)",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("gravel")),
            Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("PL"),))),
            PartOfSpeech("n"),
            "gravel",
        ),
        Entry(
            None,
            Tags.from_set_and_lang(set(), Lang("ultra-modern")),
            Fusion(Lexeme("gravel")),
            Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("DIST-PL"),))),
            PartOfSpeech("n"),
            "gravel (ultra-modern)",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("pile")),
            Component(Fusion(Morpheme("ma"))),
            PartOfSpeech("n"),
            "pile",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("gravel"), (), (Suffix("PL"),)),
            Component(Fusion(Morpheme("ka"))),
            PartOfSpeech("n"),
            "gravel (plural)",
        ),
    }

    assert parsed_lexicon.affixes == {
        AffixDefinition(
            stressed=False,
            tags=Tags(frozenset({Tag("lang")})),
            affix=Suffix("PL"),
            era=None,
            form=Component(Fusion(Morpheme("iki", Rule("era1")))),
            sources=(Lexeme("big"), Lexeme("pile")),
            description="plural for inanimate",
        ),
        AffixDefinition(
            stressed=False,
            tags=Tags(frozenset({Tag("lang")})),
            affix=Suffix("COL"),
            era=None,
            form=Component(Fusion(Morpheme(form="ma", era=None))),
            sources=(),
            description="collective",
        ),
        AffixDefinition(
            stressed=False,
            tags=Tags(),
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
            tags=Tags(frozenset({Tag("lang")})),
            era=None,
            form=Component(
                Fusion(
                    stem=Lexeme(name="stone").with_lang(),
                    prefixes=(),
                    suffixes=(Suffix("COL"),),
                )
            ),
            sources=(),
            description="made of stone",
        ),
        AffixDefinition(
            stressed=False,
            tags=Tags(),
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
            Tags(),
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
    assert parse(include, "include '/an/absolute/path'") == Path("/an/absolute/path")


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


def test_template() -> None:
    assert parse(template, "template &name $") == Template(
        TemplateName("name"), Tags(), (Var(),)
    )
    assert parse(template, "template &name { foo bar:baz } %modern $") == Template(
        TemplateName("name"),
        Tags.from_set_and_lang({Tag("foo"), Tag("bar", "baz")}, Lang("modern")),
        (Var(),),
    )
