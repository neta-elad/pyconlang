from pathlib import Path

import pytest

from pyconlang.config import Config, config_as
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
from pyconlang.lexicon.errors import MissingLexeme

from .. import default_compound


def test_resolve(root_config: Config, parsed_lexicon: Lexicon) -> None:
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
        Component(Fusion(Lexeme("council").with_scope())), Scope("ultra-modern")
    ) == Component(Morpheme("sama"))


def test_resolve_fusions(root_config: Config, parsed_lexicon: Lexicon) -> None:
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

    assert parsed_lexicon.resolve(
        Component(
            DefaultFusion(
                Lexeme("eat").with_scope(),
                (Scoped(Prefix("1SG")), Scoped(Prefix("2SG"))),
            )
        )
    ) == Compound(Component(Morpheme("mo")), Joiner.tail(), Component(Morpheme("ta")))


def test_templates(root_config: Config, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.get_vars(None) == (VarFusion("$", (), ()),)

    assert parsed_lexicon.get_vars(TemplateName("plural")) == (
        VarFusion("$", (), ()),
        VarFusion("$", (), (Scoped(Suffix("PL")),)),
    )


def test_define(root_config: Config, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.define(Scoped(Suffix("PL"))) == "plural for inanimate"

    assert parsed_lexicon.define(Scoped(Lexeme("stone"))) == "(n.) stone, pebble"


def test_form(root_config: Config, parsed_lexicon: Lexicon) -> None:
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


def test_lookup(root_config: Config, parsed_lexicon: Lexicon) -> None:
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


def test_scopes(root_config: Config, parsed_lexicon: Lexicon) -> None:
    assert parsed_lexicon.parent(Scope("modern")) == Scope()
    assert parsed_lexicon.parent(Scope("ultra-modern")) == Scope("modern")
    assert parsed_lexicon.changes_for(Scope()) == Path("src/archaic.lsc")
    assert parsed_lexicon.changes_for(Scope("modern")) == Path("src/modern.lsc")
    assert parsed_lexicon.changes_for(Scope("ultra-modern")) == Path(
        "src/ultra-modern.lsc"
    )


def test_default_scope(
    root_config: Config, modern_config: Config, sample_lexicon: str
) -> None:
    root_scope = Scope(root_config.scope)
    modern_scope = Scope(modern_config.scope)
    with config_as(root_config):
        parsed_lexicon = Lexicon.from_string(sample_lexicon)
        assert (
            parsed_lexicon.get_entry(Lexeme("pile"), root_scope).tags.scope
            == root_scope
        )
        assert (
            parsed_lexicon.get_entry(Lexeme("pile"), modern_scope).tags.scope
            == root_scope
        )

    with config_as(modern_config):
        parsed_lexicon = Lexicon.from_string(sample_lexicon)
        assert (
            parsed_lexicon.get_entry(Lexeme("pile"), modern_scope).tags.scope
            == modern_scope
        )
        with pytest.raises(MissingLexeme):
            parsed_lexicon.get_entry(Lexeme("pile"), root_scope)


def test_scope_from_filename(
    root_config: Config, modern_config: Config, sample_lexicon: str, cd_tmp_path: Path
) -> None:
    root_scope = Scope(root_config.scope)
    modern_scope = Scope(modern_config.scope)
    root_file = cd_tmp_path / f"{root_scope}"
    modern_file = cd_tmp_path / f"{modern_scope}"
    root_file.write_text(sample_lexicon)
    modern_file.write_text(sample_lexicon)

    root_lexicon = Lexicon.from_path(root_file)
    assert root_lexicon.get_entry(Lexeme("pile"), root_scope).tags.scope == root_scope
    assert root_lexicon.get_entry(Lexeme("pile"), modern_scope).tags.scope == root_scope

    modern_lexicon = Lexicon.from_path(modern_file)
    assert (
        modern_lexicon.get_entry(Lexeme("pile"), modern_scope).tags.scope
        == modern_scope
    )
    with pytest.raises(MissingLexeme):
        modern_lexicon.get_entry(Lexeme("pile"), root_scope)
