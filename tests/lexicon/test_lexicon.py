from pathlib import Path

from pyconlang.domain import (
    Component,
    Compound,
    DefaultFusion,
    Fusion,
    Joiner,
    Lexeme,
    Morpheme,
    Prefix,
    Rule,
    Scope,
    Scoped,
    Suffix,
)
from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.domain import TemplateName, VarFusion

from .. import default_compound


def test_resolve(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.resolve(
        Component(
            Fusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("DIST-PL")),))
        )
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_scope())), Scope("modern")
    ) == Component(Morpheme("kapa"))

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_scope(Scope("modern")))), Scope()
    ) == Component(Morpheme("kapa"))

    assert parsed_lexicon.resolve(
        Component(
            Fusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("DIST-PL")),))
        ),
        Scope("modern"),
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(
            Fusion(
                Lexeme("stone").with_scope(Scope("modern")),
                (),
                (Scoped(Suffix("DIST-PL")),),
            )
        ),
        Scope(),
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(
            Fusion(
                Lexeme("stone").with_scope(Scope()), (), (Scoped(Suffix("DIST-PL")),)
            )
        ),
        Scope("modern"),
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("gravel").with_scope(), (), ())), Scope("ultra-modern")
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(),
        Compound(Component(Morpheme("iki")), Joiner.head(), Component(Morpheme("ma"))),
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("PL")),)))
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.resolve(
        Component(
            Fusion(
                Lexeme("stone").with_scope(),
                (),
                (
                    Scoped(Suffix("COL")),
                    Scoped(
                        Suffix(
                            "PL",
                        )
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
        Component(Fusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("LARGE")),)))
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.resolve(
        Component(
            Fusion(
                Lexeme("stone").with_scope(),
                (),
                (Scoped(Suffix("LARGE"), Scope("modern")),),
            )
        )
    ) == Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ha")))

    assert parsed_lexicon.resolve(
        Compound(
            Component(Fusion(Lexeme("stone").with_scope())),
            Joiner.tail(),
            Component(Fusion(Morpheme("baka"))),
        )
    ) == Compound(
        Component(Morpheme("apak")), Joiner.tail(), Component(Morpheme("baka"))
    )

    assert parsed_lexicon.resolve(
        Component(Fusion(Morpheme("mana"), (Scoped(Prefix("STONE")),)))
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.tail(),
        Component(Morpheme("mana")),
    )
    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme(str(Prefix("STONE"))).with_scope()))
    ) == Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma")))

    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("dust").with_scope())), Scope("ultra-modern")
    ) == Compound(
        Component(Morpheme("kapa")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )


def test_resolve_fusions(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.resolve(
        Component(Fusion(Lexeme("gravel").with_scope(), (), (Scoped(Suffix("PL")),)))
    ) == Component(Morpheme("ka"))

    assert parsed_lexicon.resolve(
        Component(
            DefaultFusion(
                Lexeme("gravel").with_scope(),
                (Scoped(Prefix("STONE")),),
                (Scoped(Suffix("PL")),),
            )
        )
    ) == Compound(
        Compound(Component(Morpheme("apak")), Joiner.head(), Component(Morpheme("ma"))),
        Joiner.tail(),
        Component(Morpheme("ka")),
    )


def test_substitute_var(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.substitute(
        VarFusion("$", (), ()), Component(Fusion(Morpheme("apak")))
    ) == Component(Morpheme("apak"))

    assert parsed_lexicon.substitute(
        VarFusion("$", (), (Scoped(Suffix("PL")),)), Component(Fusion(Morpheme("apak")))
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.substitute(
        VarFusion("$", (), ()),
        Component(
            DefaultFusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("PL")),))
        ),
    ) == Compound(
        Component(Morpheme("apak")),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )

    assert parsed_lexicon.substitute(
        VarFusion("$", (), (Scoped(Suffix("PL")),)),
        Component(
            DefaultFusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("PL")),))
        ),
    ) == Compound(
        Compound(
            Component(Morpheme("apak")),
            Joiner.head(Rule("era1")),
            Component(Morpheme("iki", Rule("era1"))),
        ),
        Joiner.head(Rule("era1")),
        Component(Morpheme("iki", Rule("era1"))),
    )


def test_templates(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.get_vars(None) == (VarFusion("$", (), ()),)

    assert parsed_lexicon.get_vars(TemplateName("plural")) == (
        VarFusion("$", (), ()),
        VarFusion("$", (), (Scoped(Suffix("PL")),)),
    )


def test_define(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.define(Scoped(Suffix("PL"))) == "plural for inanimate"

    assert parsed_lexicon.define(Scoped(Lexeme("stone"))) == "(n.) stone, pebble"


def test_form(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.form(Scoped(Suffix("PL"))) == Scoped(
        Component(DefaultFusion(Morpheme(form="iki", era=Rule(name="era1"))))
    )

    assert parsed_lexicon.form(Scoped(Lexeme("gravel"))) == Scoped(
        Component(
            DefaultFusion(
                stem=Lexeme(name="stone").with_scope(),
                prefixes=(),
                suffixes=(Scoped(Suffix(name="PL")),),
            )
        )
    )


def test_lookup(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.lookup(Suffix("PL")) == [
        (Suffix("PL"), "plural for inanimate")
    ]

    assert parsed_lexicon.lookup(Lexeme("stone")) == [
        (Lexeme("stone"), "(n.) stone, pebble")
    ]

    assert parsed_lexicon.lookup(Morpheme("baka")) == [(Morpheme("baka"), "*baka")]

    fusion = Component(DefaultFusion(Lexeme("stone").with_scope()))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        )
    ]

    fusion = Component(DefaultFusion(Morpheme("baka")))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        )
    ]

    fusion = Component(
        DefaultFusion(Lexeme("stone").with_scope(), (), (Scoped(Suffix("PL")),))
    )
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        ),
        (Suffix("PL"), "plural for inanimate"),
    ]

    fusion = Component(DefaultFusion(Morpheme("baka"), (), (Scoped(Suffix("PL")),)))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        ),
        (Suffix("PL"), "plural for inanimate"),
    ]

    compound = default_compound(
        Component(Fusion(Morpheme("baka"), (), (Scoped(Suffix("PL")),))),
        Joiner.head(),
        Component(Fusion(Lexeme("stone").with_scope())),
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


def test_scopes(root_metadata: None, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.parent(Scope("modern")) == Scope()
    assert parsed_lexicon.parent(Scope("ultra-modern")) == Scope("modern")
    assert parsed_lexicon.changes_for(Scope()) == Path("changes/archaic.lsc")
    assert parsed_lexicon.changes_for(Scope("modern")) == Path("changes/modern.lsc")
    assert parsed_lexicon.changes_for(Scope("ultra-modern")) == Path(
        "changes/ultra-modern.lsc"
    )
