import string
from itertools import chain
from typing import Any, Dict, List, Match, Tuple, Union
from xml.etree.ElementTree import Element

from markdown import Extension, Markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.preprocessors import Preprocessor

from ..evolve import Evolved, evolve
from ..lexicon import Lexicon, parse_lexicon_file
from ..types import AffixType, Entry, Form, ResolvedForm


class LexiconPreprocessor(Preprocessor):
    extension: "LexiconInserter"

    def __init__(self, md: Markdown, extension: "LexiconInserter") -> None:
        super().__init__(md)
        self.extension = extension

    @property
    def lexicon(self) -> Lexicon:
        return self.extension.lexicon

    def run(self, lines: List[str]) -> List[str]:
        new_lines = []
        for line in lines:
            if line.strip() == "!lexicon":
                lexicon: Dict[str, List[Tuple[List[Evolved], Entry]]] = {}
                for entry in self.lexicon.entries:
                    evolved = self.evolve_all(entry)
                    letter = evolved[0].modern[0]
                    lexicon.setdefault(letter, [])
                    lexicon[letter].append((evolved, entry))
                for letter in string.ascii_lowercase:
                    new_lines.append(f"## {letter.upper()}")

                    if letter not in lexicon:
                        continue

                    lexicon[letter].sort(
                        key=lambda lexicon_entry: lexicon_entry[0][0].modern
                    )
                    for evolved, entry in lexicon[letter]:
                        protos = " + ".join(
                            f"_\\*{proto}_" for proto in self.form_to_protos(entry.form)
                        )
                        all_evolved = ", ".join(
                            f"**{each.modern}**" for each in evolved
                        )
                        new_lines.append(
                            f"""
                        {all_evolved} [{evolved[0].phonetic}] {protos} ({entry.part_of_speech.name}.) {entry.definition}
                        """.strip()
                        )
                        new_lines.append("")
            else:
                new_lines.append(line)
        return new_lines

    def form_to_protos(self, form: Form) -> List[str]:
        return self.resolved_form_to_protos(self.lexicon.resolve(form))

    def resolved_form_to_protos(self, form: ResolvedForm) -> List[str]:
        protos = [[form.stem.form]]
        for affix in form.affixes:
            affix_protos = self.resolved_form_to_protos(affix.form)
            if affix.affix.type is AffixType.PREFIX:
                protos.insert(0, affix_protos)
            else:
                protos.append(affix_protos)

        return list(chain(*protos))

    def evolve_all(self, entry: Entry) -> List[Evolved]:
        return [
            evolve(self.lexicon.substitute(var, entry.form))
            for var in self.lexicon.get_vars(entry.template)
        ]


class LexiconInlineProcessor(InlineProcessor):
    extension: "LexiconInserter"

    def __init__(self, extension: "LexiconInserter") -> None:
        super().__init__(r"#(.*?)#")
        self.extension = extension

    @property
    def lexicon(self) -> Lexicon:
        return self.extension.lexicon

    # InlineProcessor and its parent Pattern
    # have contradictory type annotations,
    # so we have to ignore type.
    def handleMatch(  # type: ignore
        self, m: Match[str], data: Any
    ) -> Union[Tuple[Element, int, int], Tuple[None, None, None]]:
        element = Element("span")
        element.text = self.evolve(m.group(1))
        return element, m.start(), m.end()

    def evolve(self, raw: str) -> str:
        return " ".join(evolved.modern for evolved in self.lexicon.evolve_string(raw))


class LexiconInserter(Extension):
    lexicon: Lexicon

    def __init__(self) -> None:
        super().__init__()

        self.lexicon = parse_lexicon_file()

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.preprocessors.register(LexiconPreprocessor(md, self), "lexicon", 0)
        md.inlinePatterns.register(LexiconInlineProcessor(self), "inline-lexicon", 200)

    def reset(self) -> None:
        self.lexicon = parse_lexicon_file()
