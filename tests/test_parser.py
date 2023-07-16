from typing import Any

from pyparsing import ParserElement

from pyconlang.domain import (
    Component,
    Compound,
    Fusion,
    Joiner,
    Lang,
    Lexeme,
    Morpheme,
    Prefix,
    Rule,
    Sentence,
    Suffix,
)
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


def test_continue_lines() -> None:
    assert list(
        continue_lines(["a", "b", " c", "d", "\t e", "", "f", "", " g", "\t h"])
    ) == ["a", "b c", "d\t e", "f", " g\t h"]


def test_base_unit() -> None:
    assert parse(rule, "@era1") == Rule("era1")
    assert parse(lexeme, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(base_unit, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(morpheme, "*proto") == Morpheme("proto")
    assert parse(base_unit, "*proto") == Morpheme("proto")
    assert parse(morpheme, "*protó") == Morpheme("protó")
    assert parse(base_unit, "*protó") == Morpheme("protó")
    assert parse(morpheme, "*proto@era1") == Morpheme("proto", Rule("era1"))
    assert parse(base_unit, "*proto@era1") == Morpheme("proto", Rule("era1"))


def test_fusion() -> None:
    assert parse(fusion, "DEF.<stone>.PL.ACC") == Fusion(
        Lexeme("stone"),
        (Prefix("DEF"),),
        (
            Suffix("PL"),
            Suffix("ACC"),
        ),
    )

    assert parse(fusion, "DEF.<stone>.PL.ACC") == Fusion(
        Lexeme("stone"),
        (Prefix("DEF"),),
        (
            Suffix("PL"),
            Suffix("ACC"),
        ),
    )

    assert parse(fusion, "*proto@era1") == Fusion(Morpheme("proto", Rule("era1")))

    assert parse(fusion, "DEF.*proto@era1.PL") == Fusion(
        Morpheme("proto", Rule("era1")),
        (Prefix("DEF"),),
        (Suffix("PL"),),
    )


def test_joiner() -> None:
    assert parse(joiner, "!+") == Joiner.head()
    assert parse(joiner, "+!") == Joiner.tail()
    assert parse(joiner, "!+@foo") == Joiner.head(Rule("foo"))
    assert parse(joiner, "+!@bar") == Joiner.tail(Rule("bar"))


def test_compound() -> None:
    assert parse(compound, "*foo") == Component(Fusion(Morpheme("foo"), ()))
    assert parse(compound, "*foo +! *bar") == Compound(
        Component(Fusion(Morpheme("foo"), ())),
        Joiner.tail(),
        Component(Fusion(Morpheme("bar"))),
    )
    assert parse(compound, "*foo !+@era *bar") == Compound(
        Component(Fusion(Morpheme("foo"), ())),
        Joiner.head(Rule("era")),
        Component(Fusion(Morpheme("bar"))),
    )
    assert parse(compound, '"*foo !+@era *bar"') == Compound(
        Component(Fusion(Morpheme("foo"), ())),
        Joiner.head(Rule("era")),
        Component(Fusion(Morpheme("bar"))),
    )
    assert parse(compound, '"*foo +!@era *bar" !+ *baz') == Compound(
        Compound(
            Component(Fusion(Morpheme("foo"), ())),
            Joiner.tail(Rule("era")),
            Component(Fusion(Morpheme("bar"))),
        ),
        Joiner.head(),
        Component(Fusion(Morpheme("baz"))),
    )


def test_sentence() -> None:
    assert parse_sentence("*aka <strong> COL.<with space> *taka@start.PL") == Sentence(
        Lang(),
        [
            Component(Fusion(Morpheme("aka"))),
            Component(Fusion(Lexeme("strong"), ())),
            Component(Fusion(Lexeme("with space"), (Prefix("COL"),), ())),
            Component(Fusion(Morpheme("taka", Rule("start")), (), (Suffix("PL"),))),
        ],
    )

    assert parse_sentence(
        "%test *aka <strong> COL.<with space> *taka@start.PL"
    ) == Sentence(
        Lang("test"),
        [
            Component(Fusion(Morpheme("aka"))),
            Component(Fusion(Lexeme("strong"), ())),
            Component(Fusion(Lexeme("with space"), (Prefix("COL"),), ())),
            Component(Fusion(Morpheme("taka", Rule("start")), (), (Suffix("PL"),))),
        ],
    )


def test_definables() -> None:
    assert parse_definables("<strong> COL. .PL").words == [
        Lexeme("strong"),
        Prefix("COL"),
        Suffix("PL"),
    ]

    assert parse_definables("%modern <strong> COL. .PL").lang == Lang("modern")


def parse(parser: ParserElement, string: str) -> Any:
    return parser.parse_string(string, parse_all=True)[0]
