import sys
import time
from pathlib import Path
from string import Template

from markdown import Markdown
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .. import PYCONLANG_PATH
from ..metadata import Metadata
from .block import Boxed, Details
from .lexicon_inserter import LexiconInserter
from .multi import MultiExtension
from .preprocess import SkipLine


class Compiler:
    converter: Markdown
    lexicon: LexiconInserter

    def __init__(self) -> None:
        self.lexicon = LexiconInserter()
        self.converter = Markdown(
            extensions=[
                "extra",
                "smarty",
                "toc",
                "sane_lists",
                "mdx_include",
                "pymdownx.escapeall",
                "pymdownx.caret",
                "pymdownx.tilde",
                SkipLine(),
                self.lexicon,
                Boxed(),
                Details(),
                MultiExtension(""),
            ],
            extension_configs={
                "mdx_include": {
                    "syntax_left": r"@\{",
                    "syntax_right": r"\}@",
                    "content_cache_clean_local": True,
                    "recursive_relative_path": True,
                }
            },
        )

    def compile(self) -> None:
        template = Template(Path("template.html").read_text())
        input_markdown = Path("book.md").read_text()
        self.converter.reset()
        content = Template(self.converter.convert(input_markdown))

        metadata = Metadata.default().to_dict()

        metadata["content"] = content.safe_substitute(**metadata)

        (PYCONLANG_PATH / "output.html").write_text(
            template.safe_substitute(**metadata)
        )

        self.lexicon.save()


class Handler(PatternMatchingEventHandler):
    compiler: Compiler

    def __init__(self) -> None:
        super().__init__(["*.md", "*.lsc", "template.html", "lexicon.txt"])
        self.compiler = Compiler()
        self.compiler.compile()

    def on_any_event(self, event: FileSystemEvent) -> None:
        print("Compiling book... ", end="")
        sys.stdout.flush()
        self.compiler.compile()
        print("Done")


def watch() -> None:
    observer = Observer()
    observer.schedule(Handler(), ".", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return
    finally:
        observer.stop()
        observer.join()


def compile_book() -> None:
    Compiler().compile()
