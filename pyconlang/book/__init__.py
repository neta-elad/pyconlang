import sys
import time
from pathlib import Path
from string import Template

from markdown import Markdown
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .. import PYCONLANG_PATH
from ..metadata import Metadata
from .block import Boxed
from .inline import InlineDelete, InlineInsert
from .lexicon_inserter import LexiconInserter
from .preprocess import SkipLine


class Compiler:
    converter: Markdown

    def __init__(self) -> None:
        self.converter = Markdown(
            extensions=[
                "extra",
                "smarty",
                "toc",
                "sane_lists",
                "mdx_include",
                SkipLine(),
                LexiconInserter(),
                InlineDelete(),
                InlineInsert(),
                Boxed(),
            ],
            extension_configs={
                "mdx_include": {
                    "syntax_left": r"@\{",
                    "syntax_right": r"\}@",
                    "content_cache_clean_local": True,
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
