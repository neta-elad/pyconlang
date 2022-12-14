from pyconlang.types import (
    Affix,
    AffixType,
    Compound,
    CompoundStress,
    Fusion,
    Lexeme,
    Morpheme,
    ResolvedAffix,
    ResolvedForm,
    Rule,
    TemplateName,
    Var,
)


def test_parsed_lexicon(parsed_lexicon):
    assert parsed_lexicon.resolve(
        Fusion(Lexeme("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == ResolvedForm(
        Morpheme("apak"),
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
        Compound(Lexeme("stone"), CompoundStress.TAIL, None, Morpheme("baka"))
    ) == ResolvedForm(
        Morpheme("apak"),
        (
            ResolvedAffix(
                True, AffixType.SUFFIX, None, ResolvedForm(Morpheme("baka"), ())
            ),
        ),
    )


def test_substitute_var(parsed_lexicon):
    assert parsed_lexicon.substitute(Var(()), Morpheme("apak")) == ResolvedForm(
        Morpheme("apak"),
        (),
    )

    assert parsed_lexicon.substitute(
        Var((Affix("PL", AffixType.SUFFIX),)), Morpheme("apak")
    ) == ResolvedForm(
        Morpheme("apak"),
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
        Var(()), Fusion(Lexeme("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == ResolvedForm(
        Morpheme("apak"),
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
        Var((Affix("PL", AffixType.SUFFIX),)),
        Fusion(Lexeme("stone"), (Affix("PL", AffixType.SUFFIX),)),
    ) == ResolvedForm(
        Morpheme("apak"),
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
    assert parsed_lexicon.get_vars(None) == (Var(()),)

    assert parsed_lexicon.get_vars(TemplateName("plural")) == (
        Var(()),
        Var((Affix("PL", AffixType.SUFFIX),)),
    )


def test_lookup(parsed_lexicon):
    assert parsed_lexicon.lookup(Affix("PL", AffixType.SUFFIX)) == [
        (Affix("PL", AffixType.SUFFIX), "plural for inanimate")
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

    fusion = Fusion(Lexeme("stone"), (Affix("PL", AffixType.SUFFIX),))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        ),
        (Affix("PL", AffixType.SUFFIX), "plural for inanimate"),
    ]

    fusion = Fusion(Morpheme("baka"), (Affix("PL", AffixType.SUFFIX),))
    assert parsed_lexicon.lookup(fusion) == [
        (
            Morpheme("baka"),
            "*baka",
        ),
        (Affix("PL", AffixType.SUFFIX), "plural for inanimate"),
    ]

    compound = Compound(
        Fusion(Morpheme("baka"), (Affix("PL", AffixType.SUFFIX),)),
        CompoundStress.HEAD,
        None,
        Lexeme("stone"),
    )
    assert parsed_lexicon.lookup(compound) == [
        (
            Morpheme("baka"),
            "*baka",
        ),
        (Affix("PL", AffixType.SUFFIX), "plural for inanimate"),
        (
            Lexeme("stone"),
            "(n.) stone, pebble",
        ),
    ]
