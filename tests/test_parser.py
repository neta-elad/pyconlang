from pyconlang.parser import base_unit, fusion, lexeme, morpheme, parse_sentence, rule
from pyconlang.types import Affix, AffixType, Fusion, Lexeme, Morpheme, Rule


def test_base_unit():
    assert parse(rule, "@era1") == Rule("era1")
    assert parse(lexeme, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(base_unit, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(morpheme, "*proto") == Morpheme("proto")
    assert parse(base_unit, "*proto") == Morpheme("proto")
    assert parse(morpheme, "*protó") == Morpheme("protó")
    assert parse(base_unit, "*protó") == Morpheme("protó")
    assert parse(morpheme, "*proto@era1") == Morpheme("proto", Rule("era1"))
    assert parse(base_unit, "*proto@era1") == Morpheme("proto", Rule("era1"))


def test_fusion():
    assert parse(fusion, "DEF.<stone>.PL.ACC") == Fusion(
        Lexeme("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(fusion, "DEF.<stone>.PL.ACC") == Fusion(
        Lexeme("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(fusion, "*proto@era1") == Fusion(Morpheme("proto", Rule("era1")))

    assert parse(fusion, "DEF.*proto@era1.PL") == Fusion(
        Morpheme("proto", Rule("era1")),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
        ),
    )


def test_sentence():
    assert tuple(parse_sentence("*aka <strong> COL.<with space> *taka@start.PL")) == (
        Fusion(Morpheme("aka")),
        Fusion(Lexeme("strong"), ()),
        Fusion(Lexeme("with space"), (Affix("COL", AffixType.PREFIX),)),
        Fusion(Morpheme("taka", Rule("start")), (Affix("PL", AffixType.SUFFIX),)),
    )


def parse(parser, string):
    return parser.parse_string(string, parse_all=True)[0]
