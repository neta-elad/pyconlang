from typing import TypeVar

import pytest

from pyconlang.domain import (
    Component,
    Fusion,
    Joiner,
    Lexeme,
    Morpheme,
    Prefix,
    Rule,
    Scope,
    ScopedLexeme,
    Suffix,
    Tag,
    Tags,
    default_compound,
    default_sentence,
)
from pyconlang.errors import DoubleTagDefinition
from pyconlang.parser import (
    base_unit,
    continue_lines,
    default_fusion,
    default_word,
    joiner,
    lexeme,
    morpheme,
    opt_tags,
    parse_definables,
    parse_sentence,
    rule,
    scope,
    scoped_lexeme,
)
from pyconlang.pyrsec import Parser

U = TypeVar("U", covariant=True)


def test_continue_lines() -> None:
    assert list(
        continue_lines(["a", "b", " c", "d", "\t e", "", "f", "", " g", "\t h"])
    ) == ["a", "b c", "d\t e", "f", " g\t h"]


def test_scope() -> None:
    assert parse(scope, "%%") is None
    assert parse(scope, "%") == Scope()
    assert parse(scope, "%modern") == Scope("modern")
    assert parse(scope, "% modern") == Scope()


def test_base_unit() -> None:
    assert parse(rule, "@era1") == Rule("era1")
    assert parse(lexeme, "<name of the-form>") == Lexeme("name of the-form")
    assert parse(scoped_lexeme, "<name of the-form>%") == Lexeme(
        "name of the-form"
    ).scoped(Scope())
    assert parse(scoped_lexeme, "<name of the-form>%") == ScopedLexeme(
        Lexeme("name of the-form"), Scope()
    )
    assert parse(scoped_lexeme, "<name of the-form>%modern") == ScopedLexeme(
        Lexeme("name of the-form"), Scope("modern")
    )
    assert parse(base_unit, "<name of the-form>%modern") == Lexeme(
        "name of the-form"
    ).scoped(Scope("modern"))
    assert parse(morpheme, "*proto") == Morpheme("proto")
    assert parse(base_unit, "*proto") == Morpheme("proto")
    assert parse(morpheme, "*protó") == Morpheme("protó")
    assert parse(base_unit, "*protó") == Morpheme("protó")
    assert parse(morpheme, "*proto@era1") == Morpheme("proto", Rule("era1"))
    assert parse(base_unit, "*proto@era1") == Morpheme("proto", Rule("era1"))


def test_fusion() -> None:
    assert parse(default_fusion, "DEF.<stone>%modern.PL.ACC") == Fusion(
        Lexeme("stone").scoped(Scope("modern")),
        (Prefix("DEF"),),
        (
            Suffix("PL"),
            Suffix("ACC"),
        ),
    )

    assert parse(default_fusion, "DEF.<stone>.PL.ACC") == Fusion(
        Lexeme("stone").scoped(),
        (Prefix("DEF"),),
        (
            Suffix("PL"),
            Suffix("ACC"),
        ),
    )

    assert parse(default_fusion, "*proto@era1") == Fusion(
        Morpheme("proto", Rule("era1"))
    )

    assert parse(default_fusion, "DEF.*proto@era1.PL") == Fusion(
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
    assert parse(default_word, "*foo") == Component(Fusion(Morpheme("foo"), ()))
    assert parse(default_word, "*foo +! *bar") == default_compound(
        Component(Fusion(Morpheme("foo"), ())),
        Joiner.tail(),
        Component(Fusion(Morpheme("bar"))),
    )
    assert parse(default_word, "*foo !+@era *bar") == default_compound(
        Component(Fusion(Morpheme("foo"), ())),
        Joiner.head(Rule("era")),
        Component(Fusion(Morpheme("bar"))),
    )
    assert parse(default_word, '"*foo !+@era *bar"') == default_compound(
        Component(Fusion(Morpheme("foo"), ())),
        Joiner.head(Rule("era")),
        Component(Fusion(Morpheme("bar"))),
    )
    assert parse(default_word, '"*foo +!@era *bar" !+ *baz') == default_compound(
        default_compound(
            Component(Fusion(Morpheme("foo"), ())),
            Joiner.tail(Rule("era")),
            Component(Fusion(Morpheme("bar"))),
        ),
        Joiner.head(),
        Component(Fusion(Morpheme("baz"))),
    )


def test_sentence() -> None:
    assert parse_sentence(
        "*aka <strong> COL.<with space> *taka@start.PL"
    ) == default_sentence(
        Tags(),
        [
            Component(Fusion(Morpheme("aka"))),
            Component(Fusion(Lexeme("strong").scoped(), ())),
            Component(Fusion(Lexeme("with space").scoped(), (Prefix("COL"),), ())),
            Component(Fusion(Morpheme("taka", Rule("start")), (), (Suffix("PL"),))),
        ],
    )

    assert parse_sentence(
        "%test *aka <strong> COL.<with space> *taka@start.PL"
    ) == default_sentence(
        Tags.from_set_and_scope(set(), Scope("test")),
        [
            Component(Fusion(Morpheme("aka"))),
            Component(Fusion(Lexeme("strong").scoped(), ())),
            Component(Fusion(Lexeme("with space").scoped(), (Prefix("COL"),), ())),
            Component(Fusion(Morpheme("taka", Rule("start")), (), (Suffix("PL"),))),
        ],
    )

    assert parse_sentence(
        "{scope:test} *aka <strong> COL.<with space> *taka@start.PL"
    ) == default_sentence(
        Tags.from_set_and_scope(set(), Scope("test")),
        [
            Component(Fusion(Morpheme("aka"))),
            Component(Fusion(Lexeme("strong").scoped(), ())),
            Component(Fusion(Lexeme("with space").scoped(), (Prefix("COL"),), ())),
            Component(Fusion(Morpheme("taka", Rule("start")), (), (Suffix("PL"),))),
        ],
    )


def test_definables() -> None:
    assert parse_definables("<strong> COL. .PL").words == [
        Lexeme("strong"),
        Prefix("COL"),
        Suffix("PL"),
    ]

    assert parse_definables("%modern <strong> COL. .PL").scope == Scope("modern")


def test_tags() -> None:
    assert parse(opt_tags, "") == Tags()

    assert parse(opt_tags, "{foo}") == Tags.from_set_and_scope({Tag("foo")})
    assert parse(opt_tags, "{foo} %%") == Tags.from_set_and_scope({Tag("foo")})
    assert parse(opt_tags, "{foo bar:baz}") == Tags.from_set_and_scope(
        {Tag("foo"), Tag("bar", "baz")}
    )
    assert parse(opt_tags, "{foo bar:baz scope:modern}") == Tags.from_set_and_scope(
        {Tag("foo"), Tag("bar", "baz")}, Scope("modern")
    )
    assert parse(opt_tags, "{foo bar:baz} %modern") == Tags.from_set_and_scope(
        {Tag("foo"), Tag("bar", "baz")}, Scope("modern")
    )
    assert parse(opt_tags, "{foo bar:baz} %") == Tags.from_set_and_scope(
        {Tag("foo"), Tag("bar", "baz")}, Scope()
    )

    with pytest.raises(DoubleTagDefinition):
        assert parse(opt_tags, "{foo foo:bar}")

    with pytest.raises(DoubleTagDefinition):
        assert parse(opt_tags, "{scope:bar} %foo")


def parse(parser: Parser[str, U], string: str) -> U:
    return parser.parse_or_raise(string)
