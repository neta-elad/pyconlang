from pyconlang.types import (
    Affix,
    AffixType,
    Canonical,
    Compound,
    Proto,
    ResolvedAffix,
    ResolvedForm,
    Rule,
    TemplateName,
    Var,
)


def test_parsed_lexicon(parsed_lexicon):
    assert parsed_lexicon.resolve(
        Compound(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == ResolvedForm(
        Proto("apak"),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
        ),
    )


def test_substitute_var(parsed_lexicon):
    assert parsed_lexicon.substitute(Var(()), Proto("apak")) == ResolvedForm(
        Proto("apak"),
        (),
    )

    assert parsed_lexicon.substitute(
        Var((Affix("PL", AffixType.SUFFIX),)), Proto("apak")
    ) == ResolvedForm(
        Proto("apak"),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.substitute(
        Var(()), Compound(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == ResolvedForm(
        Proto("apak"),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.substitute(
        Var((Affix("PL", AffixType.SUFFIX),)),
        Compound(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),)),
    ) == ResolvedForm(
        Proto("apak"),
        (
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
            ResolvedAffix(
                False,
                AffixType.SUFFIX,
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
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
    assert (
        parsed_lexicon.lookup_record(Affix("PL", AffixType.SUFFIX))
        == "plural for inanimate"
    )

    assert parsed_lexicon.lookup_record(Canonical("stone")) == "(n.) stone, pebble"

    assert parsed_lexicon.lookup_record(Proto("baka")) == "*baka"

    assert parsed_lexicon.lookup(Compound(Canonical("stone"))) == [
        (
            "<stone>",
            "(n.) stone, pebble",
        )
    ]

    assert parsed_lexicon.lookup(Compound(Proto("baka"))) == [
        (
            "*baka",
            "*baka",
        )
    ]

    assert parsed_lexicon.lookup(
        Compound(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == [
        (
            "<stone>",
            "(n.) stone, pebble",
        ),
        (".PL", "plural for inanimate"),
    ]

    assert parsed_lexicon.lookup(
        Compound(Proto("baka"), (Affix("PL", AffixType.SUFFIX),))
    ) == [
        (
            "*baka",
            "*baka",
        ),
        (".PL", "plural for inanimate"),
    ]
