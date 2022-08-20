from pyconlang.types import (
    Affix,
    AffixType,
    Canonical,
    Fusion,
    Proto,
    ResolvedAffix,
    ResolvedForm,
    Rule,
    TemplateName,
    Var,
)


def test_parsed_lexicon(parsed_lexicon):
    assert parsed_lexicon.resolve(
        Fusion(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == ResolvedForm(
        Proto("apak", None),
        (
            ResolvedAffix(
                False,
                Affix("PL", AffixType.SUFFIX),
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
        ),
    )


def test_substitute_var(parsed_lexicon):
    assert parsed_lexicon.substitute(Var(()), Proto("apak", None)) == ResolvedForm(
        Proto("apak", None),
        (),
    )

    assert parsed_lexicon.substitute(
        Var((Affix("PL", AffixType.SUFFIX),)), Proto("apak", None)
    ) == ResolvedForm(
        Proto("apak", None),
        (
            ResolvedAffix(
                False,
                Affix("PL", AffixType.SUFFIX),
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.substitute(
        Var(()), Fusion(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),))
    ) == ResolvedForm(
        Proto("apak", None),
        (
            ResolvedAffix(
                False,
                Affix("PL", AffixType.SUFFIX),
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
        ),
    )

    assert parsed_lexicon.substitute(
        Var((Affix("PL", AffixType.SUFFIX),)),
        Fusion(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),)),
    ) == ResolvedForm(
        Proto("apak", None),
        (
            ResolvedAffix(
                False,
                Affix("PL", AffixType.SUFFIX),
                Rule("era1"),
                ResolvedForm(Proto("iki", Rule("era1")), ()),
            ),
            ResolvedAffix(
                False,
                Affix("PL", AffixType.SUFFIX),
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
