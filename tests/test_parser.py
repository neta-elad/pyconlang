from pyconlang.parser import (
    canonical,
    compound,
    parse_sentence,
    proto,
    rule,
    simple_form,
)
from pyconlang.types import Affix, AffixType, Canonical, Compound, Proto, Rule


def test_simple_form():
    assert parse(rule, "@era1") == Rule("era1")
    assert parse(canonical, "<name of the-form>") == Canonical("name of the-form")
    assert parse(simple_form, "<name of the-form>") == Canonical("name of the-form")
    assert parse(proto, "*proto") == Proto("proto")
    assert parse(simple_form, "*proto") == Proto("proto")
    assert parse(proto, "*protó") == Proto("protó")
    assert parse(simple_form, "*protó") == Proto("protó")
    assert parse(proto, "*proto@era1") == Proto("proto", Rule("era1"))
    assert parse(simple_form, "*proto@era1") == Proto("proto", Rule("era1"))


def test_compound():
    assert parse(compound, "DEF.<stone>.PL.ACC") == Compound(
        Canonical("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(compound, "DEF.<stone>.PL.ACC") == Compound(
        Canonical("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(compound, "*proto@era1") == Compound(Proto("proto", Rule("era1")))

    assert parse(compound, "DEF.*proto@era1.PL") == Compound(
        Proto("proto", Rule("era1")),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
        ),
    )


def test_sentence():
    assert tuple(parse_sentence("*aka <strong> COL.<with space> *taka@start.PL")) == (
        Compound(Proto("aka")),
        Compound(Canonical("strong"), ()),
        Compound(Canonical("with space"), (Affix("COL", AffixType.PREFIX),)),
        Compound(Proto("taka", Rule("start")), (Affix("PL", AffixType.SUFFIX),)),
    )


def parse(parser, string):
    return parser.parse_string(string, parse_all=True)[0]
