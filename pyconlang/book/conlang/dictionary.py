import re

from markdown import Markdown
from markdown.preprocessors import Preprocessor

from ... import CHANGES_GLOB, CHANGES_PATH, LEXICON_GLOB, LEXICON_PATH
from ...cache import path_cached_property
from ...lexicon.domain import Entry, VarFusion
from ...translate import Translator


class ConlangGrouper(Preprocessor):
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

    @staticmethod
    def order_group(groups: list[str]) -> list[str]:
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


class ConlangDictionary(Preprocessor):
    translator: Translator
    cache: list[str]

    def __init__(self, md: Markdown, translator: Translator) -> None:
        super().__init__(md)

        self.translator = translator
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

    @path_cached_property(LEXICON_PATH, LEXICON_GLOB, CHANGES_PATH, CHANGES_GLOB)
    def dictionary(self) -> list[str]:
        return self.build_cache()

    def build_cache(self) -> list[str]:
        return list(map(self.show_entry, self.translator.lexicon.entries))

    def show_entry(self, entry: Entry) -> str:
        # sources = _join_morphemes(self.translator.lexicon.resolve(entry.form))

        forms = [
            f"r[{self.show_var(var, str(entry.form))}]"
            for var in self.translator.lexicon.get_vars(entry.template)
        ]

        return (
            ", ".join(forms)
            + f" [ph({entry.form})] pr[{entry.form}] {entry.description()}"
        )

    @staticmethod
    def show_var(var: VarFusion, stem: str) -> str:
        for affix in var.prefixes + var.suffixes:
            stem = affix.combine(stem, affix.name)

        return stem
