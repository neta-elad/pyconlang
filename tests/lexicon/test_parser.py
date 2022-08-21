from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.parser import (
    affix,
    affix_definition,
    canonical,
    compound,
    entry,
    lexical_sources,
    parse_sentence,
    part_of_speech,
    proto,
    rule,
    simple_form,
    template_name,
    var,
)
from pyconlang.types import (
    Affix,
    AffixDefinition,
    AffixType,
    Canonical,
    Compound,
    Entry,
    PartOfSpeech,
    Proto,
    Rule,
    Template,
    TemplateName,
    Var,
)


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


def test_affix():
    assert parse(affix, ".PL") == Affix("PL", AffixType.SUFFIX)
    assert parse(affix, "PL.") == Affix("PL", AffixType.PREFIX)


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


def test_entry_parts():
    assert parse(template_name, "&template") == TemplateName("template")
    assert parse(part_of_speech, "(adj.)") == PartOfSpeech("adj")


def test_entry():
    assert parse(entry, "entry <strong> *kipu@era1 (adj.) strong, stable") == Entry(
        None,
        Canonical("strong"),
        Compound(Proto("kipu", Rule("era1"))),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> *kipu@era1.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Canonical("strong"),
        Compound(Proto("kipu", Rule("era1")), (Affix("PL", AffixType.SUFFIX),)),
        PartOfSpeech("adj"),
        "strong, stable",
    )

    assert parse(
        entry, "entry &plural <strong> <heavy>.PL (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Canonical("strong"),
        Compound(Canonical("heavy"), (Affix("PL", AffixType.SUFFIX),)),
        PartOfSpeech("adj"),
        "strong, stable",
    )


def test_affix_definition():
    assert parse(lexical_sources, "(<big> <pile>)") == (
        Canonical("big"),
        Canonical("pile"),
    )

    assert parse(
        affix_definition, "affix ! .PL @era *proto (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        True,
        Affix("PL", AffixType.SUFFIX),
        Rule("era"),
        Proto("proto"),
        (Canonical("big"), Canonical("pile")),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL *proto@era plural for inanimate"
    ) == AffixDefinition(
        False,
        Affix("PL", AffixType.SUFFIX),
        None,
        Proto("proto", Rule("era")),
        (),
        "plural for inanimate",
    )

    assert parse(
        affix_definition, "affix .PL (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        False,
        Affix("PL", AffixType.SUFFIX),
        None,
        None,
        (Canonical("big"), Canonical("pile")),
        "plural for inanimate",
    )


def test_lexicon(parsed_lexicon):
    assert isinstance(parsed_lexicon, Lexicon)

    assert frozenset(parsed_lexicon.entries) == frozenset(
        {
            Entry(
                None,
                Canonical("strong"),
                Compound(Proto("kipu", Rule("era1"))),
                PartOfSpeech("adj"),
                "strong, stable",
            ),
            Entry(
                None,
                Canonical("big"),
                Compound(Proto("iki")),
                PartOfSpeech("adj"),
                "big, great",
            ),
            Entry(
                TemplateName("plural"),
                Canonical("stone"),
                Compound(Proto("apak")),
                PartOfSpeech("n"),
                "stone, pebble",
            ),
            Entry(
                None,
                Canonical("gravel"),
                Compound(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),)),
                PartOfSpeech("n"),
                "gravel",
            ),
        }
    )

    assert frozenset(parsed_lexicon.affixes) == frozenset(
        {
            AffixDefinition(
                False,
                Affix("PL", AffixType.SUFFIX),
                None,
                Proto("iki", Rule("era1")),
                (Canonical("big"), Canonical("pile")),
                "plural for inanimate",
            )
        }
    )

    assert frozenset(parsed_lexicon.templates) == frozenset(
        {
            Template(
                TemplateName("plural"), (Var(()), Var((Affix("PL", AffixType.SUFFIX),)))
            )
        }
    )


def test_var(sample_lexicon):
    assert parse(var, "$") == Var(())
    assert parse(var, "$.PL") == Var((Affix("PL", AffixType.SUFFIX),))
    assert parse(var, "DEF.$.PL.COL") == Var(
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("COL", AffixType.SUFFIX),
        )
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
