import re

from markdown import Extension, Markdown
from markdown.preprocessors import Preprocessor


class UnicodeEscape(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)

        md.preprocessors.register(UnicodeEscapePreprocessor(md), "unicode-escape", 15)


class UnicodeEscapePreprocessor(Preprocessor):
    UNICODE_ESCAPE = re.compile(r"\\u(?P<code>[0-9A-Fa-f]{4,})")

    def run(self, lines: list[str]) -> list[str]:
        return [self.map_line(line) for line in lines]

    def map_line(self, line: str) -> str:
        return self.UNICODE_ESCAPE.sub(self.map_match, line)

    def map_match(self, match: re.Match[str]) -> str:
        code = match.group("code")

        return chr(int(f"0x{code}", 0))
