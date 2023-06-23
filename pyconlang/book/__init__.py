import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from string import Template
from threading import Thread
from typing import Self

from markdown import Markdown
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .. import PYCONLANG_PATH
from ..metadata import Metadata
from ..translate import Translator
from .abbreviation import Abbreviation
from .any_table_header import AnyTableHeader
from .block import Boxed, Details
from .lexicon_inserter import LexiconInserter
from .multi import MultiExtension
from .preprocess import SkipLine
from .ruby import Ruby
from .span_table import SpanTable
from .unicode import UnicodeEscape


class Compiler:
    converter: Markdown
    lexicon: LexiconInserter

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with Translator.new() as translator:
            yield cls(translator)

    def __init__(self, translator: Translator) -> None:
        self.lexicon = LexiconInserter(translator)
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
                Boxed(),
                Details(),
                MultiExtension(""),
                SpanTable(),
                AnyTableHeader(),
                Abbreviation(),
                Ruby(),
                self.lexicon,
                UnicodeEscape(),
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


class Handler(PatternMatchingEventHandler):
    silent: bool
    compiler: Compiler
    last_run: float
    last_request: float
    running: bool
    threads: list[Thread]

    def __init__(self, compiler: Compiler, silent: bool = False):
        super().__init__(["*.md", "*.lsc", "template.html", "*.pycl"])
        self.compiler = compiler
        self.silent = silent
        self.last_run = 0.0
        self.last_request = time.time()
        self.running = False
        self.threads = []
        self.compile()

    def on_any_event(self, event: FileSystemEvent) -> None:
        self.last_request = time.time()
        self.compile()

    def compile(self) -> None:
        self.threads.append(Thread(target=self.compile_thread))
        self.threads[-1].start()

    def compile_thread(self) -> None:
        if self.last_run >= self.last_request or self.running:
            return

        self.running = True

        if not self.silent:
            print("Compiling book... ", end="")
            sys.stdout.flush()

        self.compiler.compile()
        self.last_run = time.time()
        self.running = False

        self.compile()

        if not self.silent:
            print("Done")

    def join(self) -> None:
        for thread in self.threads:
            thread.join()


def watch() -> None:
    with Compiler.new() as compiler:
        handler = Handler(compiler)
        observer = Observer()
        observer.schedule(handler, ".", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return
        finally:
            observer.stop()
            observer.join()
            handler.join()


def compile_book() -> None:
    with Compiler.new() as compiler:
        compiler.compile()
