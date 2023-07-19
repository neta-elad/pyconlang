from pathlib import Path

from pyconlang import CHANGES_PATH
from pyconlang.domain import (
    Component,
    Compound,
    Fusion,
    Joiner,
    Lang,
    Lexeme,
    Morpheme,
    Prefix,
    Rule,
    Suffix,
    default_compound,
)
from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.domain import TemplateName, Var


def test_resolve(parsed_lexicon: Lexicon, tmp_pyconlang: Path) -> None:
    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("DIST-PL"),)))
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang())), Lang("modern")
    ) == Component(Morpheme("kapa"))

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang(Lang("modern")))), Lang()
    ) == Component(Morpheme("kapa"))

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("DIST-PL"),))),
        Lang("modern"),
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(
            Fusion(Lexeme("stone").with_lang(Lang("modern")), (), (Suffix("DIST-PL"),))
        ),
        Lang(),
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang(Lang()), (), (Suffix("DIST-PL"),))),
        Lang("modern"),
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("gravel").with_lang(), (), ())), Lang("ultra-modern")
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("PL"),)))
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.resolve(
        Component(
            Fusion(
                Lexeme("stone").with_lang(),
                (),
                (
                    Suffix("COL"),
                    Suffix(
                        "PL",
                    ),
                ),
            )
        )
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("LARGE"),)))
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.resolve(
        Compound(
            Component(Fusion(Lexeme("stone").with_lang())),
            Joiner.tail(),
            Component(Fusion(Morpheme("baka"))),
        )
    ) == Compound(
        Component(Morpheme("apak")), Joiner.tail(), Component(Morpheme("baka"))
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Morpheme("mana"), (Prefix("STONE"),)))
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.tail(),
        Component(Morpheme("mana")),
    )
    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme(str(Prefix("STONE"))).with_lang()))
    ) == Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma")))


def test_resolve_fusions(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("gravel").with_lang(), (), (Suffix("PL"),)))
    ) == Component(Morpheme("ka"))

    assert parsed_lexicon.resolve(
        Component(
            Fusion(Lexeme("gravel").with_lang(), (Prefix("STONE"),), (Suffix("PL"),))
        )
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.tail(),
        Component(Morpheme("ka")),
    )


def test_substitute_var(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.substitute(
        Var((), ()), Component(Fusion(Morpheme("apak")))
    ) == Component(Morpheme("apak"))

    assert parsed_lexicon.substitute(
        Var((), (Suffix("PL"),)), Component(Fusion(Morpheme("apak")))
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.substitute(
        Var((), ()), Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("PL"),)))
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.substitute(
        Var((), (Suffix("PL"),)),
        Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("PL"),))),
    ) == Compound(
        Compound(
            Component(Morpheme("apak")),
            Joiner.head(Rule("era1")),
            Component(Morpheme("iki", Rule("era1"))),
        ),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )


def test_templates(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.get_vars(None) == (Var((), ()),)

    assert parsed_lexicon.get_vars(TemplateName("plural")) == (
        Var((), ()),
        Var((), (Suffix("PL"),)),
    )


def test_define(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.define(Suffix("PL")) == "plural for inanimate"

    assert parsed_lexicon.define(Lexeme("stone")) == "(n.) stone, pebble"


def test_form(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.form(Suffix("PL")) == Component(
        Fusion(Morpheme(form="iki", era=Rule(name="era1")))
    )

    assert parsed_lexicon.form(Lexeme("gravel")) == Component(
        Fusion(
            stem=Lexeme(name="stone").with_lang(),
            prefixes=(),
            suffixes=(Suffix(name="PL"),),
        )
    )


def test_resolve_definable(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.resolve_definable(Suffix("PL")) == Component(
        Morpheme("iki", Rule("era1"))
    )

    assert parsed_lexicon.resolve_definable(Lexeme("gravel")) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )


def test_lookup(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.lookup(Suffix("PL")) == [
        (Suffix("PL"), "plural for inanimate")
    ]

    assert parsed_lexicon.lookup(Lexeme("stone")) == [
        (Lexeme("stone"), "(n.) stone, pebble")
    ]

    assert parsed_lexicon.lookup(Morpheme("baka")) == [(Morpheme("baka"), "*baka")]

    fusion = Component(Fusion(Lexeme("stone").with_lang()))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        )
    ]

    fusion = Component(Fusion(Morpheme("baka")))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        )
    ]

    fusion = Component(Fusion(Lexeme("stone").with_lang(), (), (Suffix("PL"),)))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        ),
        (Suffix("PL"), "plural for inanimate"),
    ]

    fusion = Component(Fusion(Morpheme("baka"), (), (Suffix("PL"),)))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        ),
        (Suffix("PL"), "plural for inanimate"),
    ]

    compound = default_compound(
        Component(Fusion(Morpheme("baka"), (), (Suffix("PL"),))),
        Joiner.head(),
        Component(Fusion(Lexeme("stone").with_lang())),
    )
    assert parsed_lexicon.lookup(compound) == [
        (
            Morpheme("baka"),
            "*baka",
        ),
        (Suffix("PL"), "plural for inanimate"),
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        ),
    ]


def test_langs(parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.parent(Lang("modern")) == Lang()
    assert parsed_lexicon.parent(Lang("ultra-modern")) == Lang("modern")
    assert parsed_lexicon.changes_for(Lang()) == CHANGES_PATH
    assert parsed_lexicon.changes_for(Lang("modern")) == CHANGES_PATH
    assert parsed_lexicon.changes_for(Lang("ultra-modern")) == Path("ultra-modern.lsc")
