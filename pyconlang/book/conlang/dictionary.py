import re

from markdown import Markdown
from markdown.preprocessors import Preprocessor

from ... import CHANGES_GLOB, CHANGES_PATH, LEXICON_GLOB, LEXICON_PATH
from ...cache import path_cached_method
from ...domain import Scope
from ...lexicon.domain import AffixDefinition, Entry, VarFusion
from ...parser import scope as scope_parser
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
            match = re.search(r"(\w|')", line)
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
    cache: dict[Scope, list[str]]
    pattern: re.Pattern[str]

    def __init__(self, md: Markdown, translator: Translator) -> None:
        super().__init__(md)

        self.translator = translator
        self.pattern = re.compile(r"^!dictionary:(?P<scope>%[A-Za-z0-9-]*|%%)$")

    def run(self, lines: list[str]) -> list[str]:
        new_lines = []
        for line in lines:
            if (match := re.match(self.pattern, line.strip())) is not None:
                raw_scope = match.group("scope")
                parsed_scope = scope_parser.parse_or_raise(raw_scope)
                new_lines.append("!group")
                new_lines.extend(self.show_scope(parsed_scope or Scope.default()))
                new_lines.append("!group")
            else:
                new_lines.append(line)

        return new_lines

    @path_cached_method(LEXICON_PATH, LEXICON_GLOB, CHANGES_PATH, CHANGES_GLOB)
    def show_scope(self, scope: Scope) -> list[str]:
        return list(
            map(
                self.show_entry,
                self.translator.lexicon.entries_by_scope[scope],
            )
        )

    @path_cached_method(LEXICON_PATH, LEXICON_GLOB, CHANGES_PATH, CHANGES_GLOB)
    def show_entry(self, entry: Entry) -> str:
        scope = entry.tags.scope
        form = str(entry.lexeme)
        forms = [
            f"r[{scope} {self.show_var(var, form)}]"
            for var in self.translator.lexicon.get_vars(entry.template)
        ]

        return (
            ", ".join(forms)
            + f" [ph({scope} {form})] pr[{scope} {form}] {entry.description()}"
        )

    @staticmethod
    def show_var(var: VarFusion, stem: str) -> str:
        for prefix in var.prefixes:
            stem = f"{prefix}{stem}"
        for suffix in var.suffixes:
            stem = f"{stem}{suffix}"

        return stem


class ConlangAffixes(Preprocessor):
    translator: Translator
    cache: dict[Scope, list[str]]
    pattern: re.Pattern[str]

    def __init__(self, md: Markdown, translator: Translator) -> None:
        super().__init__(md)

        self.translator = translator
        self.pattern = re.compile(r"^!affixes:(?P<scope>%[A-Za-z0-9-]*|%%)$")

    def run(self, lines: list[str]) -> list[str]:
        new_lines = []
        for line in lines:
            if (match := re.match(self.pattern, line.strip())) is not None:
                raw_scope = match.group("scope")
                parsed_scope = scope_parser.parse_or_raise(raw_scope)
                new_lines.extend(self.show_scope(parsed_scope or Scope.default()))
            else:
                new_lines.append(line)

        return new_lines

    @path_cached_method(LEXICON_PATH, LEXICON_GLOB, CHANGES_PATH, CHANGES_GLOB)
    def show_scope(self, scope: Scope) -> list[str]:
        if scope not in self.translator.lexicon.affixes_by_scope:
            return []

        return ["|Affix|Description|Sources|", "|-|-|-|"] + list(
            map(
                self.show_affix,
                sorted(
                    self.translator.lexicon.affixes_by_scope[scope],
                    key=lambda affix: affix.description,
                ),
            )
        )

    @path_cached_method(LEXICON_PATH, LEXICON_GLOB, CHANGES_PATH, CHANGES_GLOB)
    def show_affix(self, affix: AffixDefinition) -> str:
        form = str(affix.to_scoped_lexeme_fusion())
        combined = affix.affix.combine("-", f"ph[{form}]", "")
        sources = ", ".join(map(lambda source: f"pr[{source}]", affix.sources))

        return f"|{combined}|{affix.description}|{sources}|"
