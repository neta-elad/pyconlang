from inspect import cleandoc
from pathlib import Path

import pytest

from pyconlang.domain import (
    Component,
    Compound,
    Fusion,
    Joiner,
    Lexeme,
    Morpheme,
    PartOfSpeech,
    Prefix,
    Rule,
    Scope,
    Scoped,
    Suffix,
    Tag,
    Tags,
)
from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.domain import (
    AffixDefinition,
    Entry,
    ScopeDefinition,
    Template,
    TemplateName,
    VarFusion,
)
from pyconlang.lexicon.parser import (
    affix_definition,
    comment,
    entry,
    include,
    lexical_sources,
    lexicon_line,
    part_of_speech,
    quoted_string,
    scope_definition,
    template,
    template_name,
    var,
)
from pyconlang.parser import affix
from pyconlang.pyrsec import PyrsecError

from ..test_parser import parse


def test_entry_parts() -> None:
    assert parse(template_name, "&template") == TemplateName("template")
    assert parse(part_of_speech, "(adj.)") == PartOfSpeech("adj")


def test_entry() -> None:
    assert parse(entry, "entry <strong> *kipu@era1 (adj.) strong, stable") == Entry(
        None,
        Tags(),
        Fusion(Lexeme("strong")),
        Scoped(Component(Fusion(Morpheme("kipu", Rule("era1"))))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> *kipu@era1.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Tags(),
        Fusion(Lexeme("strong")),
        Scoped(
            Component(
                Fusion(Morpheme("kipu", Rule("era1")), (), (Scoped(Suffix("PL")),))
            )
        ),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> <heavy>.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Tags(),
        Fusion(Lexeme("strong")),
        Scoped(
            Component(Fusion(Lexeme("heavy").with_scope(), (), (Scoped(Suffix("PL")),)))
        ),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry %ultra-modern <dust> % <gravel>.PL (n.) dust, sand"
    ) == Entry(
        None,
        Tags(frozenset({Tag("scope", "ultra-modern")})),
        Fusion(Lexeme("dust")),
        Scoped(
            Component(
                Fusion(Lexeme("gravel").with_scope(), (), (Scoped(Suffix("PL")),))
            ),
            Scope(),
        ),
        PartOfSpeech("n"),
        "dust, sand",
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
        form=Scoped(Component(Fusion(Morpheme("proto")))),
        sources=(Lexeme("big"), Lexeme("pile")),
        description="plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL *proto@era plural for inanimate"
    ) == AffixDefinition(
        stressed=False,
        tags=Tags(),
        affix=Suffix("PL"),
        form=Scoped(Component(Fusion(Morpheme("proto", Rule("era"))))),
        description="plural for inanimate",
    )

    assert parse(
        affix_definition,
        "affix { foo bar:baz } .PL (<big> <pile>) plural for inanimate",
    ) == AffixDefinition(
        stressed=False,
        affix=Suffix("PL"),
        tags=Tags.from_set_and_scope({Tag("foo"), Tag("bar", "baz")}),
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
        form=Scoped(
            Component(Fusion(Lexeme("big").with_scope(), (), (Scoped(Suffix("PL")),)))
        ),
        sources=(),
        description="collective form",
    )

    assert parse(
        affix_definition, "affix COL. { <big> !+ <pile>.PL } collective form"
    ) == AffixDefinition(
        stressed=False,
        tags=Tags(),
        affix=Prefix("COL"),
        era=None,
        form=Scoped(
            Compound(
                Component(Fusion(Lexeme("big").with_scope())),
                Joiner.head(),
                Component(
                    Fusion(Lexeme("pile").with_scope(), (), (Scoped(Suffix("PL")),))
                ),
            )
        ),
        sources=(),
        description="collective form",
    )


def test_comment() -> None:
    assert parse(comment, "# <nothing at all *..") == "# <nothing at all *.."
    assert parse(comment, "   ### <nothing at all *..") == "   ### <nothing at all *.."


def test_scope() -> None:
    assert parse(scope_definition, "scope %modern : %%") == ScopeDefinition(
        Scope("modern"), Scope()
    )

    assert parse(scope_definition, "scope %ultra-modern : %modern") == ScopeDefinition(
        Scope("ultra-modern"), Scope("modern")
    )

    assert parse(
        scope_definition, "scope %ultra-modern : %modern 'changes/ultra-modern.lsc'"
    ) == ScopeDefinition(
        Scope("ultra-modern"), Scope("modern"), Path("changes") / "ultra-modern.lsc"
    )


def test_lexicon_line() -> None:
    assert parse(
        lexicon_line, "scope %ultra-modern : %modern 'changes/ultra-modern.lsc'"
    ) == ScopeDefinition(
        Scope("ultra-modern"), Scope("modern"), Path("changes") / "ultra-modern.lsc"
    )

    assert parse(lexicon_line, "template &name $") == Template(
        TemplateName("name"), Tags(), (VarFusion("$"),)
    )

    assert parse(
        lexicon_line, "affix ! .PL @era *proto (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        stressed=True,
        tags=Tags(),
        affix=Suffix("PL"),
        era=Rule("era"),
        form=Scoped(Component(Fusion(Morpheme("proto")))),
        sources=(Lexeme("big"), Lexeme("pile")),
        description="plural for inanimate",
    )

    assert parse(
        lexicon_line, "entry &plural <strong> *kipu@era1.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Tags(),
        Fusion(Lexeme("strong")),
        Scoped(
            Component(
                Fusion(Morpheme("kipu", Rule("era1")), (), (Scoped(Suffix("PL")),))
            )
        ),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(lexicon_line, " \t\n") is None
    assert parse(lexicon_line, " \t # and a comment") is None


def test_errors() -> None:
    with pytest.raises(PyrsecError) as e:
        parse(lexicon_line, "lang bla")

    assert e.value.index == 0
    assert e.value.expected == "eof"

    with pytest.raises(PyrsecError) as e:
        parse(lexicon_line, "entry <bla *ka")

    assert e.value.index == 14
    assert e.value.expected == ">"


def test_lexicon(parsed_lexicon: Lexicon) -> None:
    assert isinstance(parsed_lexicon, Lexicon)

    assert parsed_lexicon.entries == {
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("strong")),
            Scoped(Component(Fusion(Morpheme("kipu", Rule("era1"))))),
            PartOfSpeech("adj"),
            "strong, stable",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("big")),
            Scoped(Component(Fusion(Morpheme("iki")))),
            PartOfSpeech("adj"),
            "big, great",
        ),
        Entry(
            None,
            Tags(frozenset({Tag("scope")})),
            Fusion(Lexeme("big"), (), (Suffix("PL"),)),
            Scoped(Component(Fusion(Morpheme("sama")))),
            PartOfSpeech("adj"),
            "large people",
        ),
        Entry(
            TemplateName("plural"),
            Tags(frozenset({Tag("scope")})),
            Fusion(Lexeme("stone")),
            Scoped(Component(Fusion(Morpheme("apak")))),
            PartOfSpeech("n"),
            "stone, pebble",
        ),
        Entry(
            None,
            Tags(frozenset({Tag("scope", "modern")})),
            Fusion(Lexeme("stone")),
            Scoped(Component(Fusion(Morpheme("kapa")))),
            PartOfSpeech("n"),
            "stone, pebble (modern)",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("gravel")),
            Scoped(
                Component(
                    Fusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("PL")),))
                )
            ),
            PartOfSpeech("n"),
            "gravel",
        ),
        Entry(
            None,
            Tags.from_set_and_scope(set(), Scope("ultra-modern")),
            Fusion(Lexeme("gravel")),
            Scoped(
                Component(
                    Fusion(
                        Lexeme("stone").with_scope(), (), (Scoped(Suffix("DIST-PL")),)
                    )
                )
            ),
            PartOfSpeech("n"),
            "gravel (ultra-modern)",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("pile")),
            Scoped(Component(Fusion(Morpheme("ma")))),
            PartOfSpeech("n"),
            "pile",
        ),
        Entry(
            None,
            Tags(),
            Fusion(Lexeme("gravel"), (), (Suffix("PL"),)),
            Scoped(Component(Fusion(Morpheme("ka")))),
            PartOfSpeech("n"),
            "gravel (plural)",
        ),
        Entry(
            None,
            Tags(frozenset({Tag("scope", "ultra-modern")})),
            Fusion(Lexeme("council")),
            Scoped(
                Component(
                    Fusion(Lexeme("big").with_scope(), (), (Scoped(Suffix("PL")),))
                ),
                Scope(),
            ),
            PartOfSpeech("n"),
            "council",
        ),
    }

    assert parsed_lexicon.affixes == {
        AffixDefinition(
            stressed=False,
            tags=Tags(frozenset({Tag("scope")})),
            affix=Suffix("PL"),
            era=None,
            form=Scoped(Component(Fusion(Morpheme("iki", Rule("era1"))))),
            sources=(Lexeme("big"), Lexeme("pile")),
            description="plural for inanimate",
        ),
        AffixDefinition(
            stressed=False,
            tags=Tags(frozenset({Tag("scope")})),
            affix=Suffix("COL"),
            era=None,
            form=Scoped(Component(Fusion(Morpheme(form="ma", era=None)))),
            sources=(),
            description="collective",
        ),
        AffixDefinition(
            stressed=False,
            tags=Tags(frozenset({Tag("scope", "modern")})),
            affix=Suffix("LARGE"),
            era=None,
            form=Scoped(Component(Fusion(Morpheme("ha")))),
            sources=(),
            description="large object",
        ),
        AffixDefinition(
            stressed=False,
            tags=Tags(),
            affix=Suffix("LARGE"),
            era=None,
            form=VarFusion(
                "$",
                prefixes=(),
                suffixes=(
                    Scoped(Suffix("COL")),
                    Scoped(Suffix("PL")),
                ),
            ),
            sources=(),
            description="large plural",
        ),
        AffixDefinition(
            stressed=False,
            affix=Prefix("STONE"),
            tags=Tags(frozenset({Tag("scope")})),
            era=None,
            form=Scoped(
                Component(
                    Fusion(
                        stem=Lexeme(name="stone").with_scope(),
                        prefixes=(),
                        suffixes=(Scoped(Suffix("COL")),),
                    )
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
            (VarFusion("$", (), ()), VarFusion("$", (), (Scoped(Suffix("PL")),))),
        )
    }


def test_var() -> None:
    assert parse(var, "$") == VarFusion("$", (), ())
    assert parse(var, "$.PL") == VarFusion("$", (), (Scoped(Suffix("PL")),))
    assert parse(var, "DEF.$.PL.COL") == VarFusion(
        "$",
        (Scoped(Prefix("DEF")),),
        (
            Scoped(Suffix("PL")),
            Scoped(Suffix("COL")),
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
        TemplateName("name"), Tags(), (VarFusion("$"),)
    )
    assert parse(template, "template &name { foo bar:baz } %modern $") == Template(
        TemplateName("name"),
        Tags.from_set_and_scope({Tag("foo"), Tag("bar", "baz")}, Scope("modern")),
        (VarFusion("$"),),
    )
