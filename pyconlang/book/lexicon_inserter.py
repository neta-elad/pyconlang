import re
from abc import ABCMeta, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from itertools import chain
from typing import Self

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

from .. import CHANGES_PATH, LEXICON_PATH
from ..cache import path_cached_property
from ..domain import (
    Definable,
    Entry,
    Fusion,
    Lexeme,
    Morpheme,
    Prefix,
    ResolvedForm,
    Suffix,
    Word,
)
from ..evolve.domain import Evolved
from ..translate import Translator


class LexiconInserter(Extension):
    translator: Translator

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with Translator.new() as translator:
            yield cls(translator)

    def __init__(self, translator: Translator) -> None:
        super().__init__()

        self.translator = translator
        self.valid_cache = False

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)

        md.preprocessors.register(LexiconGroupingProcessor(md), "lexicon-grouping", 15)

        md.preprocessors.register(
            LexiconRomanizedProcessor(md, self), "lexicon-romanized", 20
        )

        md.preprocessors.register(
            LexiconPhoneticProcessor(md, self), "lexicon-phonetic", 20
        )

        md.preprocessors.register(LexiconProtoProcessor(md, self), "lexicon-proto", 20)

        md.preprocessors.register(
            LexiconDefinitionProcessor(md, self), "lexicon-definition", 20
        )

        md.preprocessors.register(
            LexiconDefinitionFormProcessor(md, self), "lexicon-definition-form", 20
        )

        md.preprocessors.register(
            LexiconBatchingRomanizerProcessor(md, self), "lexicon-caching-romanizer", 21
        )

        md.preprocessors.register(
            LexiconAbbreviationProcessor(md, self), "lexicon-abbreviation", 25
        )

        md.preprocessors.register(LexiconRubyProcessor(md, self), "lexicon-ruby", 25)

        md.preprocessors.register(
            LexiconGlossTableProcessor(md, self), "lexicon-gloss-table", 26
        )

        md.preprocessors.register(
            LexiconDictionaryProcessor(md, self), "lexicon-dictionary", 30
        )

    def save(self) -> None:
        self.translator.save()


class LexiconGroupingProcessor(Preprocessor):
    def run(self, lines: list[str]) -> list[str]:
        new_lines = []
        groups: list[str] = []
        grouping = False
        for line in lines:
            if line.strip() == "!group":
                if grouping:
                    new_lines.extend(self.order_group(groups))
                    groups = []
                grouping = not grouping
                continue
            else:
                if grouping:
                    groups.append(line)
                else:
                    new_lines.append(line)

        return new_lines

    def order_group(self, groups: list[str]) -> list[str]:
        ordered_groups: dict[str, list[str]] = {}

        for line in groups:
            match = re.search(r"\w", line)
            if match is None:
                group = "-"
            else:
                group = match.group(0)

            ordered_groups.setdefault(group, [])
            ordered_groups[group].append(line)

        keys = sorted(ordered_groups.keys())

        new_lines = []

        for key in keys:
            new_lines.append(f"## {key.upper()}")
            for line in sorted(ordered_groups[key]):
                new_lines.append(line)
                new_lines.append("")

        return new_lines


class LexiconPreprocessor(Preprocessor, metaclass=ABCMeta):
    pattern: re.Pattern[str]
    inserter: LexiconInserter

    def __init__(self, md: Markdown, inserter: LexiconInserter) -> None:
        super().__init__(md)

        self.pattern = re.compile(self.expression())
        self.inserter = inserter

    @classmethod
    @abstractmethod
    def expression(cls) -> str:
        pass

    @abstractmethod
    def map_match(self, match: re.Match[str]) -> str:
        pass

    def run(self, lines: list[str]) -> list[str]:
        return [self.map_line(line) for line in lines]

    def map_line(self, line: str) -> str:
        return self.pattern.sub(self.map_match, line)


class LexiconMacroPreprocessor(LexiconPreprocessor, metaclass=ABCMeta):
    @classmethod
    def expression(cls) -> str:
        return rf"&{cls.token()}{{(?P<text>.+?)}}"

    @staticmethod
    @abstractmethod
    def token() -> str:
        pass

    @abstractmethod
    def map_text(self, text: str) -> str:
        pass

    def map_match(self, match: re.Match[str]) -> str:
        return self.map_text(match.group("text"))


class LexiconEvolveProcessor(LexiconMacroPreprocessor, metaclass=ABCMeta):
    def map_text(self, text: str) -> str:
        return " ".join(
            self.map_evolved(evolved)
            for evolved in self.inserter.translator.evolve_string(text)
        )

    @abstractmethod
    def map_evolved(self, evolved: Evolved) -> str:
        pass


class LexiconRomanizedProcessor(LexiconEvolveProcessor):
    @staticmethod
    def token() -> str:
        return "r"

    def map_evolved(self, evolved: Evolved) -> str:
        return evolved.modern


class LexiconPhoneticProcessor(LexiconEvolveProcessor):
    @staticmethod
    def token() -> str:
        return "ph"

    def map_evolved(self, evolved: Evolved) -> str:
        return evolved.phonetic


class LexiconProtoProcessor(LexiconEvolveProcessor):
    @staticmethod
    def token() -> str:
        return "pr"

    def map_evolved(self, evolved: Evolved) -> str:
        return f"\\*{evolved.proto}"


class LexiconDefinitionProcessor(LexiconMacroPreprocessor):
    @staticmethod
    def token() -> str:
        return "d"

    def map_text(self, text: str) -> str:
        return "; ".join(self.inserter.translator.define_string(text))


class LexiconDefinitionFormProcessor(LexiconMacroPreprocessor):
    @staticmethod
    def token() -> str:
        return "df"

    def map_text(self, text: str) -> str:
        return "; ".join(
            map(
                _join_morphemes, self.inserter.translator.resolve_definable_string(text)
            )
        )


class LexiconAbbreviationProcessor(LexiconPreprocessor):
    @classmethod
    def expression(cls) -> str:
        return r"\+\+(?P<definables>.+?)\+\+"

    def map_match(self, match: re.Match[str]) -> str:
        definables = match.group("definables")

        return "".join(
            map(
                self.map_definable,
                self.inserter.translator.parse_definables(definables),
            )
        )

    @staticmethod
    def map_definable(definable: Definable) -> str:
        match definable:
            case Lexeme():
                return f"+{definable.name}+&d{{{definable}}}+"
            case Prefix() | Suffix():
                return definable.combine("", f"+{definable.name}+&d{{{definable}}}+")


class LexiconBatchingRomanizerProcessor(LexiconPreprocessor):
    batch: list[str] = []

    @classmethod
    def expression(cls) -> str:
        return r"#(?P<text>[^#]+?)#"

    def run(self, lines: list[str]) -> list[str]:
        self.batch = []
        lines = super().run(lines)

        all_resolved = list(
            chain(*map(self.inserter.translator.resolve_string, self.batch))
        )
        self.inserter.translator.evolver.evolve(all_resolved)

        return lines

    def map_match(self, match: re.Match[str]) -> str:
        text = match.group("text")
        self.batch.append(text.strip())
        return f"&r{{{text}}}"


class LexiconRubyProcessor(LexiconPreprocessor):
    @classmethod
    def expression(cls) -> str:
        return r"%%(?P<text>.+?)%%"

    def map_match(self, match: re.Match[str]) -> str:
        text = match.group("text")
        return f"%&r{{{text}}}%[&ph{{{text}}}]%"


class LexiconGlossTableProcessor(LexiconPreprocessor):
    @classmethod
    def expression(cls) -> str:
        return r"##(?P<text>[^#]+?)##"

    def map_match(self, match: re.Match[str]) -> str:
        words = self.inserter.translator.parse_sentence(match.group("text").strip())

        result = (
            "|".join(f"%%{word}%%" for word in words)
            + "\n"
            + "|".join("-" for _word in words)
            + "\n"
            + "|".join(f"++{word}++" for word in words)
        )

        return result


class LexiconDictionaryProcessor(Preprocessor):
    inserter: LexiconInserter
    cache: list[str]

    def __init__(self, md: Markdown, inserter: LexiconInserter) -> None:
        super().__init__(md)

        self.inserter = inserter
        self.cache = self.build_cache()

    def run(self, lines: list[str]) -> list[str]:
        new_lines = []
        for line in lines:
            if line.strip() == "!dictionary":
                new_lines.append("!group")
                new_lines.extend(self.dictionary)
                new_lines.append("!group")
            else:
                new_lines.append(line)

        return new_lines

    @path_cached_property(CHANGES_PATH, LEXICON_PATH)
    def dictionary(self) -> list[str]:
        return self.build_cache()

    def build_cache(self) -> list[str]:
        return list(map(self.show_entry, self.inserter.translator.lexicon.entries))

    def show_entry(self, entry: Entry) -> str:
        sources = _join_morphemes(self.inserter.translator.lexicon.resolve(entry.form))

        forms = [
            f"**#{var.show(str(entry.form))}#**"
            for var in self.inserter.translator.lexicon.get_vars(entry.template)
        ]

        return (
            ", ".join(forms) + f" [&ph{{{entry.form}}}] {sources} {entry.description()}"
        )

    def form_to_morphemes(self, form: Word[Fusion]) -> list[Morpheme]:
        return self.inserter.translator.lexicon.resolve(form).leaves()


def _join_morphemes(form: ResolvedForm) -> str:
    return " \\+ ".join(f"_\\*{morpheme.form}_" for morpheme in form.leaves())
