from pyconlang.types import (
    AffixType,
    Compound,
    Fusion,
    Joiner,
    Lexeme,
    Morpheme,
    Prefix,
    ResolvedAffix,
    ResolvedForm,
    Rule,
    Suffix,
    TemplateName,
    Var,
)


def test_parsed_lexicon(parsed_lexicon):
    assert parsed_lexicon.resolve(
        Fusion(Lexeme("stone"), (), (Suffix("PL"),))
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.resolve(
        Fusion(
            Lexeme("stone"),
            (),
            (
                Suffix("COL"),
                Suffix(
                    "PL",
                ),
            ),
        )
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                None,
                ResolvedForm(Morpheme("ma", None), ()),
            ),
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.resolve(
        Fusion(Lexeme("stone"), (), (Suffix("LARGE"),))
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                None,
                ResolvedForm(Morpheme("ma", None), ()),
            ),
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.resolve(
        Compound(Lexeme("stone"), Joiner.tail(), Morpheme("baka"))
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                True, AffixType.SUFFIX, None, ResolvedForm(Morpheme("baka"), ())
            ),
        ),
    )

    assert parsed_lexicon.resolve(
        Fusion(Morpheme("mana"), (Prefix("STONE"),))
    ) == ResolvedForm(
        stem=Morpheme(form="mana", era=None),
        prefixes=(
            ResolvedAffix(
                stressed=False,
                type=AffixType.PREFIX,
                era=None,
                form=ResolvedForm(
                    stem=Morpheme(form="apak", era=None),
                    prefixes=(),
                    suffixes=(
                        ResolvedAffix(
                            stressed=False,
                            type=AffixType.SUFFIX,
                            era=None,
                            form=ResolvedForm(stem=Morpheme(form="ma", era=None)),
                        ),
                    ),
                ),
            ),
        ),
        suffixes=(),
    )


def test_substitute_var(parsed_lexicon):
    assert parsed_lexicon.substitute(Var((), ()), Morpheme("apak")) == ResolvedForm(
        Morpheme("apak"),
        (),
    )

    assert parsed_lexicon.substitute(
        Var((), (Suffix("PL"),)), Morpheme("apak")
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.substitute(
        Var((), ()), Fusion(Lexeme("stone"), (), (Suffix("PL"),))
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.substitute(
        Var((), (Suffix("PL"),)),
        Fusion(Lexeme("stone"), (), (Suffix("PL"),)),
    ) == ResolvedForm(
        Morpheme("apak"),
        (),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Morpheme("iki", Rule("era1")), ()),
            ),
        ),
    )


def test_templates(parsed_lexicon):
    assert parsed_lexicon.get_vars(None) == (Var((), ()),)

    assert parsed_lexicon.get_vars(TemplateName("plural")) == (
        Var((), ()),
        Var((), (Suffix("PL"),)),
    )


def test_define(parsed_lexicon):
    assert parsed_lexicon.define(Suffix("PL")) == "plural for inanimate"

    assert parsed_lexicon.define(Lexeme("stone")) == "(n.) stone, pebble"


def test_form(parsed_lexicon):
    assert parsed_lexicon.form(Suffix("PL")) == Fusion(
        Morpheme(form="iki", era=Rule(name="era1"))
    )

    assert parsed_lexicon.form(Lexeme("gravel")) == Fusion(
        stem=Lexeme(name="stone"),
        prefixes=(),
        suffixes=(Suffix(name="PL"),),
    )


def test_resolve_definable(parsed_lexicon):
    assert parsed_lexicon.resolve_definable(Suffix("PL")) == ResolvedForm(
        stem=Morpheme(form="iki", era=Rule(name="era1")), prefixes=(), suffixes=()
    )

    assert parsed_lexicon.resolve_definable(Lexeme("gravel")) == ResolvedForm(
        stem=Morpheme(form="apak", era=None),
        prefixes=(),
        suffixes=(
            ResolvedAffix(
                stressed=False,
                type=AffixType.SUFFIX,
                era=Rule(name="era1"),
                form=ResolvedForm(
                    stem=Morpheme(form="iki", era=Rule(name="era1")),
                ),
            ),
        ),
    )


def test_lookup(parsed_lexicon):
    assert parsed_lexicon.lookup(Suffix("PL")) == [
        (Suffix("PL"), "plural for inanimate")
    ]

    assert parsed_lexicon.lookup(Lexeme("stone")) == [
        (Lexeme("stone"), "(n.) stone, pebble")
    ]

    assert parsed_lexicon.lookup(Morpheme("baka")) == [(Morpheme("baka"), "*baka")]

    fusion = Fusion(Lexeme("stone"))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        )
    ]

    fusion = Fusion(Morpheme("baka"))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        )
    ]

    fusion = Fusion(Lexeme("stone"), (Suffix("PL"),))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        ),
        (Suffix("PL"), "plural for inanimate"),
    ]

    fusion = Fusion(Morpheme("baka"), (Suffix("PL"),))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        ),
        (Suffix("PL"), "plural for inanimate"),
    ]

    compound = Compound(
        Fusion(Morpheme("baka"), (Suffix("PL"),)),
        Joiner.head(),
        Lexeme("stone"),
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
