from collections.abc import Generator
from contextlib import contextmanager
from typing import Self

from markdown import Markdown
from markdown.extensions import Extension

from ...translate import Translator
from .advanced_macros import (
    AdvancedDefinitionMacro,
    AdvancedProtoMacro,
    GlossTableMacro,
)
from .batching_macros import BatchingPhoneticMacro, BatchingRomanizedMacro
from .before_after_macros import (
    AfterBeforePhoneticMacro,
    AfterBeforeRomanizedMacro,
    BeforeAfterPhoneticMacro,
    BeforeAfterRomanizedMacro,
)
from .dictionary import ConlangDictionary, ConlangGrouper
from .raw_macros import (
    RawDefinitionMacro,
    RawPhoneticMacro,
    RawProtoMacro,
    RawRomanizedMacro,
)


class Conlang(Extension):
    translator: Translator

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with Translator.new() as translator:
            yield cls(translator)

    def __init__(self, translator: Translator) -> None:
        super().__init__()

        self.translator = translator

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)

        md.preprocessors.register(ConlangGrouper(md), "conlang-grouper", 15)

        md.preprocessors.register(
            RawRomanizedMacro(md, self.translator), "conlang-romanized", 20
        )

        md.preprocessors.register(
            RawPhoneticMacro(md, self.translator), "conlang-phonetic", 20
        )

        md.preprocessors.register(
            RawProtoMacro(md, self.translator), "conlang-proto", 20
        )

        md.preprocessors.register(
            RawDefinitionMacro(md, self.translator), "conlang-definition", 20
        )

        md.preprocessors.register(
            BatchingRomanizedMacro(md, self.translator),
            "conlang-batching-romanized",
            25,
        )

        md.preprocessors.register(
            AdvancedProtoMacro(md, self.translator), "conlang-advanced-proto", 25
        )

        md.preprocessors.register(
            AdvancedDefinitionMacro(md, self.translator),
            "conlang-advanced-definition",
            25,
        )

        md.preprocessors.register(
            BatchingPhoneticMacro(md, self.translator), "conlang-batching-phonetic", 30
        )

        md.preprocessors.register(
            BeforeAfterRomanizedMacro(md, self.translator),
            "conlang-before-after-romanized",
            35,
        )

        md.preprocessors.register(
            BeforeAfterPhoneticMacro(md, self.translator),
            "conlang-before-after-phonetic",
            35,
        )

        md.preprocessors.register(
            AfterBeforeRomanizedMacro(md, self.translator),
            "conlang-after-before-romanized",
            35,
        )

        md.preprocessors.register(
            AfterBeforePhoneticMacro(md, self.translator),
            "conlang-after-before-phonetic",
            35,
        )

        md.preprocessors.register(
            GlossTableMacro(md, self.translator), "lexicon-gloss-table", 35
        )

        md.preprocessors.register(
            ConlangDictionary(md, self.translator), "conlang-dictionary", 40
        )
