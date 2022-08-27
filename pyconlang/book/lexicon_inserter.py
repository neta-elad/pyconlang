import string
from typing import Any, Dict, List, Match, Tuple, Union
from xml.etree.ElementTree import Element, SubElement

from markdown import Extension, Markdown
from markdown.blockparser import BlockParser
from markdown.inlinepatterns import InlineProcessor
from markdown.preprocessors import Preprocessor

from ..errors import show_exception
from ..evolve.types import Evolved
from ..translate import Translator
from ..types import Entry, Form, Proto
from .block import DelimitedProcessor


class LexiconPreprocessor(Preprocessor):
    extension: "LexiconInserter"
    cache: List[str]

    def __init__(self, md: Markdown, extension: "LexiconInserter") -> None:
        super().__init__(md)
        self.extension = extension
        self.build_cache()

    @property
    def translator(self) -> Translator:
        return self.extension.translator

    def run(self, lines: List[str]) -> List[str]:
        new_lines = []
        for line in lines:
            if line.strip() != "!lexicon":
                new_lines.append(line)
                continue

            if not self.extension.valid_cache:
                try:
                    self.build_cache()
                except Exception as e:
                    print("Could not build lexicon.")
                    print(show_exception(e))

            new_lines.extend(self.cache)

        return new_lines

    def build_cache(self) -> None:
        self.cache = []
        lexicon: Dict[str, List[Tuple[List[Evolved], Entry]]] = {}
        for entry, evolved in self.translator.batch_evolve().items():
            letter = evolved[0].modern[0]
            lexicon.setdefault(letter, [])
            lexicon[letter].append((evolved, entry))

        for letter in string.ascii_lowercase:
            self.cache.append(f"## {letter.upper()}")

            if letter not in lexicon:
                continue

            lexicon[letter].sort(key=lambda lexicon_entry: lexicon_entry[0][0].modern)
            for evolved, entry in lexicon[letter]:
                protos = " + ".join(
                    f"_\\*{proto.form}_" for proto in self.form_to_protos(entry.form)
                )
                all_evolved = ", ".join(f"**{each.modern}**" for each in evolved)
                self.cache.append(
                    f"""
                {all_evolved} [{evolved[0].phonetic}] {protos} ({entry.part_of_speech.name}.) {entry.definition}
                """.strip()
                )
                self.cache.append("")

    def form_to_protos(self, form: Form) -> List[Proto]:
        return self.translator.lexicon.resolve(form).to_protos()


class LexiconInlineProcessor(InlineProcessor):
    extension: "LexiconInserter"

    def __init__(self, extension: "LexiconInserter") -> None:
        super().__init__(r"#(.*?)#")
        self.extension = extension

    @property
    def translator(self) -> Translator:
        return self.extension.translator

    # InlineProcessor and its parent Pattern
    # have contradictory type annotations,
    # so we have to ignore type.
    def handleMatch(  # type: ignore
        self, m: Match[str], data: Any
    ) -> Union[Tuple[Element, int, int], Tuple[None, None, None]]:
        element = Element("span")
        sentence = m.group(1)
        try:
            element.text = self.evolve(sentence)
        except Exception as e:
            print(f"Could not inline from lexicon `{sentence}`")
            print(show_exception(e))
            element.text = "???"
        return element, m.start(), m.end()

    def evolve(self, raw: str) -> str:
        return " ".join(
            evolved.modern for evolved in self.translator.evolve_string(raw)
        )


class LexiconBlockProcessor(DelimitedProcessor):
    extension: "LexiconInserter"

    def __init__(self, parser: BlockParser, extension: "LexiconInserter") -> None:
        super().__init__(parser, "translate")
        self.extension = extension

    def run_inner_blocks(self, parent: Element, blocks: List[str]) -> None:
        pre = SubElement(parent, "pre")
        code = SubElement(pre, "code")

        from itertools import chain

        lines = chain(*map(str.splitlines, blocks))

        code.text = "\n".join(self.evolve(line) for line in lines)

    def evolve(self, raw: str) -> str:
        return " ".join(
            evolved.modern for evolved in self.extension.translator.evolve_string(raw)
        )


class LexiconInserter(Extension):
    translator: Translator
    valid_cache: bool

    def __init__(self) -> None:
        super().__init__()

        self.translator = Translator()
        self.valid_cache = False

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.preprocessors.register(LexiconPreprocessor(md, self), "lexicon", 0)
        md.inlinePatterns.register(LexiconInlineProcessor(self), "inline-lexicon", 200)
        md.parser.blockprocessors.register(
            LexiconBlockProcessor(md.parser, self), "block-lexicon", 200
        )

    def reset(self) -> None:
        try:
            self.valid_cache = self.translator.validate_cache()
        except Exception as e:
            print("Could not reload translator.")
            print(show_exception(e))
