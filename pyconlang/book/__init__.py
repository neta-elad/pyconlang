import shutil
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from functools import cache, cached_property
from pathlib import Path
from string import Template
from threading import Thread
from typing import Self

from markdown import Markdown
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .. import ASSETS_PATH, PYCONLANG_PATH, SRC_GLOB, SRC_PATH
from ..cache import resolve_any_path
from ..config import config, config_scope_as
from ..errors import pass_exception
from ..translate import Translator
from .any_table_header import AnyTableHeader
from .block import Boxed
from .conlang import Conlang
from .multi import MultiExtension
from .skipline import SkipLine
from .span_table import SpanTable
from .unicode import UnicodeEscape

LAYOUT_PATH = SRC_PATH / "layout.html"
OUT_PATH = PYCONLANG_PATH / "out"


class Compiler:
    conlang: Conlang

    @classmethod
    @contextmanager
    def new(cls) -> Generator[Self, None, None]:
        with pass_exception(Translator.new()) as translator:
            yield cls(translator)

    def __init__(self, translator: Translator) -> None:
        self.conlang = Conlang(translator)

    @cache
    def converter_for(self, path: Path) -> Markdown:
        return Markdown(
            extensions=[
                "extra",
                "smarty",
                "toc",
                "sane_lists",
                "mdx_include",
                "pymdownx.escapeall",
                "pymdownx.caret",
                "pymdownx.tilde",
                "pymdownx.saneheaders",
                "pymdownx.tasklist",
                "pymdownx.blocks.details",
                "pymdownx.blocks.tab",
                SkipLine(),
                Boxed(),
                MultiExtension(""),
                SpanTable(),
                AnyTableHeader(),
                UnicodeEscape(),
                self.conlang,
            ],
            extension_configs={
                "mdx_include": {
                    "base_path": str(path.parent),
                    "syntax_left": r"@\{",
                    "syntax_right": r"\}@",
                    "content_cache_clean_local": True,
                    "recursive_relative_path": True,
                }
            },
        )

    @cached_property
    def template(self) -> Template:
        return Template(LAYOUT_PATH.read_text())

    def compile(self) -> None:
        if OUT_PATH.exists():
            shutil.rmtree(OUT_PATH)
        if ASSETS_PATH.exists():
            shutil.copytree(ASSETS_PATH, OUT_PATH)
        for file in resolve_any_path(SRC_GLOB):
            self.compile_file(file)

    def compile_file(self, file: Path) -> None:
        assert file.suffixes == [".out", ".md"]
        assert file.is_relative_to(SRC_PATH)

        relative = file.relative_to(SRC_PATH)

        stem = file.stem[:-4]

        scope = config().scope
        if stem.startswith("%"):
            stem = scope = stem[1:]

        if stem == relative.parent.stem:
            relative = relative.parent

        target = OUT_PATH / relative.with_name(f"{stem}.html")

        self.converter_for(file).reset()

        with config_scope_as(scope):
            content = Template(self.converter_for(file).convert(file.read_text()))
            substitutions = config().to_dict()

        substitutions["content"] = content.safe_substitute(**substitutions)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.template.safe_substitute(**substitutions))


class Handler(PatternMatchingEventHandler):
    silent: bool
    compiler: Compiler
    last_run: float
    last_request: float
    running: bool
    threads: list[Thread]
    last_error: Exception | None

    def __init__(self, compiler: Compiler, silent: bool = False):
        super().__init__(["*.md", "*.lsc", "layout.html", "*.pycl"])
        self.compiler = compiler
        self.silent = silent
        self.last_run = 0.0
        self.last_request = time.time()
        self.running = False
        self.threads = []
        self.last_error = None
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

        try:
            self.compiler.compile()
            self.last_error = None
        except Exception as e:
            self.last_error = e

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
        observer.schedule(handler, str(SRC_PATH), recursive=True)
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
    with pass_exception(Compiler.new()) as compiler:
        compiler.compile()
