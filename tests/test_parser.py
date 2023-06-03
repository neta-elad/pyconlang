from pyconlang.parser import (
    base_unit,
    compound,
    continue_lines,
    fusion,
    joiner,
    lexeme,
    morpheme,
    parse_definables,
    parse_sentence,
    rule,
)
from pyconlang.types import (
    Affix,
    AffixType,
    Compound,
    CompoundStress,
    Fusion,
    Lexeme,
    Morpheme,
    Rule,
)


def test_continue_lines():
    assert list(
        continue_lines(["a", "b", " c", "d", "\t e", "", "f", "", " g", "\t h"])
    ) == ["a", "b c", "d\t e", "f", " g\t h"]


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


def test_compound():
    assert parse(joiner, "!+") == CompoundStress.HEAD
    assert parse(joiner, "+!") == CompoundStress.TAIL

    assert parse(compound, "*foo") == Fusion(Morpheme("foo"), ())
    assert parse(compound, "*foo +! *bar") == Compound(
        Fusion(Morpheme("foo"), ()), CompoundStress.TAIL, None, Fusion(Morpheme("bar"))
    )
    assert parse(compound, "*foo !+@era *bar") == Compound(
        Fusion(Morpheme("foo"), ()),
        CompoundStress.HEAD,
        Rule("era"),
        Fusion(Morpheme("bar")),
    )
    assert parse(compound, "[*foo !+@era *bar]") == Compound(
        Fusion(Morpheme("foo"), ()),
        CompoundStress.HEAD,
        Rule("era"),
        Fusion(Morpheme("bar")),
    )
    assert parse(compound, "[*foo +!@era *bar] !+ *baz") == Compound(
        Compound(
            Fusion(Morpheme("foo"), ()),
            CompoundStress.TAIL,
            Rule("era"),
            Fusion(Morpheme("bar")),
        ),
        CompoundStress.HEAD,
        None,
        Fusion(Morpheme("baz")),
    )


def test_sentence():
    assert tuple(parse_sentence("*aka <strong> COL.<with space> *taka@start.PL")) == (
        Fusion(Morpheme("aka")),
        Fusion(Lexeme("strong"), ()),
        Fusion(Lexeme("with space"), (Affix("COL", AffixType.PREFIX),)),
        Fusion(Morpheme("taka", Rule("start")), (Affix("PL", AffixType.SUFFIX),)),
    )


def test_definables():
    assert tuple(parse_definables("<strong> COL. .PL")) == (
        Lexeme("strong"),
        Affix("COL", AffixType.PREFIX),
        Affix("PL", AffixType.SUFFIX),
    )


def parse(parser, string):
    return parser.parse_string(string, parse_all=True)[0]
