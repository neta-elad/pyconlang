from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class SkipLinePreprocessor(Preprocessor):
    state: "SkipLine"

    def __init__(self, md: Markdown, state: "SkipLine") -> None:
        super().__init__(md)
        self.state = state

    def run(self, lines: list[str]) -> list[str]:
        kept_lines = []
        skipped_lines = []
        for line in lines:
            if line.strip().startswith("!!"):
                skipped_lines.append(line)
            else:
                kept_lines.append(line)
        self.state.skipped = skipped_lines
        return kept_lines


class SkipLine(Extension):
    skipped: list[str]

    def __init__(self) -> None:
        super().__init__()
        self.skipped = []

    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.preprocessors.register(SkipLinePreprocessor(md, self), "skipline", 1000)

    def reset(self) -> None:
        self.skipped = []
