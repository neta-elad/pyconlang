from pyconlang.lexicon import Lexicon
from pyconlang.lexicon.parser import (
    affix,
    affix_definition,
    canonical,
    entry,
    form,
    fusion,
    lexical_sources,
    part_of_speech,
    proto,
    rule,
    template_name,
    var,
)
from pyconlang.types import (
    Affix,
    AffixDefinition,
    AffixType,
    Canonical,
    Entry,
    Fusion,
    PartOfSpeech,
    Proto,
    Rule,
    Template,
    TemplateName,
    Var,
)


def test_entry():
    assert parse(rule, "@era1") == Rule("era1")
    assert parse(canonical, "<name of the-rule>") == Canonical("name of the-rule")
    assert parse(proto, "*proto") == Proto("proto", None)
    assert parse(proto, "*proto@era1") == Proto("proto", Rule("era1"))
    assert parse(template_name, "&template") == TemplateName("template")
    assert parse(part_of_speech, "(adj.)") == PartOfSpeech("adj")
    assert parse(entry, "entry <strong> *kipu@era1 (adj.) strong, stable") == Entry(
        None,
        Canonical("strong"),
        Proto("kipu", Rule("era1")),
        PartOfSpeech("adj"),
        "strong, stable",
    )
    assert parse(
        entry, "entry &plural <strong> *kipu@era1 (adj.) strong, stable"
    ) == Entry(
        TemplateName("plural"),
        Canonical("strong"),
        Proto("kipu", Rule("era1")),
        PartOfSpeech("adj"),
        "strong, stable",
    )


def test_form():
    assert parse(fusion, "DEF.<stone>.PL.ACC") == Fusion(
        Canonical("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(form, "DEF.<stone>.PL.ACC") == Fusion(
        Canonical("stone"),
        (
            Affix("DEF", AffixType.PREFIX),
            Affix("PL", AffixType.SUFFIX),
            Affix("ACC", AffixType.SUFFIX),
        ),
    )

    assert parse(form, "*proto@era1") == Proto("proto", Rule("era1"))


def test_affix():
    assert parse(affix, ".PL") == Affix("PL", AffixType.SUFFIX)
    assert parse(affix, "PL.") == Affix("PL", AffixType.PREFIX)
    assert parse(lexical_sources, "(<big> <pile>)") == (
        Canonical("big"),
        Canonical("pile"),
    )


def test_affix_definition():
    assert parse(
        affix_definition, "affix ! .PL @era *proto (<big> <pile>) plural for inanimate"
    ) == AffixDefinition(
        True,
        Affix("PL", AffixType.SUFFIX),
        Rule("era"),
        Proto("proto", None),
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
                Proto("kipu", Rule("era1")),
                PartOfSpeech("adj"),
                "strong, stable",
            ),
            Entry(
                TemplateName("plural"),
                Canonical("stone"),
                Proto("apak", None),
                PartOfSpeech("n"),
                "stone, pebble",
            ),
            Entry(
                None,
                Canonical("gravel"),
                Fusion(Canonical("stone"), (Affix("PL", AffixType.SUFFIX),)),
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


def parse(parser, string):
    return parser.parse_string(string)[0]
