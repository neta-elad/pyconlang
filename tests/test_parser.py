from pyconlang.parser import (
    compound,
    lexeme,
    morpheme,
    parse_sentence,
    rule,
    simple_form,
)
from pyconlang.types import Affix, AffixType, Compound, Lexeme, Morpheme, Rule


def test_simple_form():
    assert parse(rule, "@era1") == Rule("era1")
    assert parse(lexeme, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(simple_form, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(morpheme, "*proto") == Morpheme("proto")
    assert parse(simple_form, "*proto") == Morpheme("proto")
    assert parse(morpheme, "*protó") == Morpheme("protó")
    assert parse(simple_form, "*protó") == Morpheme("protó")
    assert parse(morpheme, "*proto@era1") == Morpheme("proto", Rule("era1"))
    assert parse(simple_form, "*proto@era1") == Morpheme("proto", Rule("era1"))


def test_compound():
    assert parse(compound, "DEF.<stone>.PL.ACC") == Compound(
        Lexeme("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(compound, "DEF.<stone>.PL.ACC") == Compound(
        Lexeme("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(compound, "*proto@era1") == Compound(Morpheme("proto", Rule("era1")))

    assert parse(compound, "DEF.*proto@era1.PL") == Compound(
        Morpheme("proto", Rule("era1")),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
        ),
    )


def test_sentence():
    assert tuple(parse_sentence("*aka <strong> COL.<with space> *taka@start.PL")) == (
        Compound(Morpheme("aka")),
        Compound(Lexeme("strong"), ()),
        Compound(Lexeme("with space"), (Affix("COL", AffixType.PREFIX),)),
        Compound(Morpheme("taka", Rule("start")), (Affix("PL", AffixType.SUFFIX),)),
    )


def parse(parser, string):
    return parser.parse_string(string, parse_all=True)[0]
