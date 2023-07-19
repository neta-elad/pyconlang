import re
from abc import ABCMeta, abstractmethod

from ...domain import Definable, Lexeme, Prefix, ResolvedForm, Suffix, Tags
from .conlang_macro import ConlangMacro


class ShortcutRomanizedMacro(ConlangMacro):
    @classmethod
    def expression(cls) -> str:
        return rf"\[\[(?P<text>.+?)\]\]"

    def map_match(self, match: re.Match[str]) -> str:
        text = match.group("text")
        return f"r[{text}]"


class AdvancedMacro(ConlangMacro, metaclass=ABCMeta):
    @classmethod
    def expression(cls) -> str:
        return rf"\b{cls.token()}\[(?P<text>.+?)\]"

    @classmethod
    @abstractmethod
    def token(cls) -> str:
        pass

    @abstractmethod
    def map_inner_text(self, text: str) -> str:
        ...

    def map_match(self, match: re.Match[str]) -> str:
        text = match.group("text")
        return self.map_inner_text(text)


class AdvancedDefinitionMacro(AdvancedMacro):
    @classmethod
    def token(cls) -> str:
        return "d"

    def map_inner_text(self, text: str) -> str:
        sentence = self.translator.parse_definables(text)
        return "".join(
            map(
                lambda word: self.map_definable(word, sentence.tags),
                sentence.words,
            )
        )

    @classmethod
    def map_definable(cls, definable: Definable, tags: Tags) -> str:
        abbr = cls.build_definition_abbr(tags, definable.name, str(definable))
        match definable:
            case Lexeme():
                return abbr
            case Prefix() | Suffix():
                return definable.combine("", abbr)

    @staticmethod
    def build_definition_abbr(tags: Tags, text: str, title: str) -> str:
        return f'<abbr title="d({tags} {title})">{text}</abbr>'


class GlossTableMacro(AdvancedMacro):
    @classmethod
    def token(cls) -> str:
        return "g"

    def map_inner_text(self, text: str) -> str:
        sentence = self.translator.parse_sentence(text.strip())
        words = sentence.words

        result = (
            "|"
            + "|".join(f"ph[{sentence.tags} {word}]" for word in words)
            + "|"
            + "\n"
            + "|"
            + "|".join("-" for _word in words)
            + "|"
            + "\n"
            + "|"
            + "|".join(f"d[{sentence.tags} {word}]" for word in words)
            + "|"
        )

        return f"&{{\n\n{result}\n\n}}{{:.gloss-table}}"


class AdvancedProtoMacro(AdvancedMacro):
    @classmethod
    def token(cls) -> str:
        return "pr"

    def map_inner_text(self, text: str) -> str:
        sentence = self.translator.parse_sentence(text.strip())
        forms = [
            self.translator.lexicon.resolve(word, sentence.scope)
            for word in sentence.words
        ]
        return " ".join(_join_morphemes(form) for form in forms)


def _join_morphemes(form: ResolvedForm) -> str:
    return " \\+ ".join(f"_\\*pr({morpheme})_" for morpheme in form.leaves())
