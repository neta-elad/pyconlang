import contextlib
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.styles import Style
from watchdog.events import FileSystemEvent
from watchdog.observers import Observer

from . import PYCONLANG_PATH
from .book import Compiler
from .book import Handler as BookHandler
from .domain import Describable
from .translate import Translator
from .unicode import center, length

HISTORY_PATH = PYCONLANG_PATH / "repl.history"


def _show_lookup_records(records: list[tuple[Describable, str]]) -> str:
    return "\n".join(
        _show_lookup_record(record, description) for record, description in records
    )


def _show_lookup_record(record: Describable, description: str) -> str:
    return f"{record}: {description}"


class Handler(BookHandler):
    changed: bool

    def __init__(self, compiler: Compiler) -> None:
        super().__init__(compiler, True)
        self.changed = False

    def on_any_event(self, event: FileSystemEvent) -> None:
        super().on_any_event(event)
        self.changed = True


@dataclass(eq=True, frozen=True)
class TranslatorAction:
    action: Callable[[Translator, str], str]

    def __call__(self, translator: Translator, line: str) -> str:
        return self.action(translator, line)


def trace(translator: Translator, line: str) -> str:
    """
    Traces the sound changes for each individual query sent to Lexurgy.
    """
    lines: list[str] = []
    for evolved, trace_set in translator.trace_string(line):
        for query, trace_lines in trace_set:
            lines.append(query)
            for trace_line in trace_lines:
                lines.append(
                    f"{trace_line.before} => {trace_line.after} ({trace_line.rule})"
                )

    return "\n".join(lines)


def translate(translator: Translator, line: str) -> str:
    """
    Translates a sentence using the lexicon and sound changes.
    Can also be used without prefixing the command.
    """
    return " ".join(
        f"{form.modern} [{form.phonetic}]" for form in translator.evolve_string(line)
    )


def gloss(translator: Translator, line: str) -> str:
    """
    Translates and glosses the translation.
    """
    lines = []
    glosses = [
        (evolved.modern, str(form)) for evolved, form in translator.gloss_string(line)
    ]

    lines.append(
        " ".join(center(pair[0], 2 + max(map(length, pair)), " ") for pair in glosses)
    )
    lines.append(
        " ".join(center(pair[1], 2 + max(map(length, pair)), " ") for pair in glosses)
    )

    return "\n".join(lines)


def lookup(translator: Translator, line: str) -> str:
    """
    Breaks down compound forms and looks them up in the lexicon.
    """
    result = translator.lookup_string(line)

    if len(result) == 1:
        return _show_lookup_records(result[0][1])
    else:
        return "\n\n".join(
            f"Records for {form}\n{_show_lookup_records(foo)}" for form, foo in result
        )


class Mode(TranslatorAction, Enum):
    NORMAL = (translate,)
    TRACE = (trace,)
    GLOSS = (gloss,)
    LOOKUP = (lookup,)


@dataclass
class ReplSession:
    translator: Translator
    watcher: Handler
    last_line: str = field(default="")
    counter: int = field(default=0)
    mode: Mode = Mode.NORMAL
    debug: str = ""

    @cached_property
    def session_style(self) -> Style:
        return Style.from_dict(
            {
                "rprompt": "bg:#bb0055 #ffffff",
            }
        )

    def on_key_press(self, event: KeyPressEvent) -> None:
        self.debug = str(event)

    @cached_property
    def session_bindings(self) -> KeyBindings:
        bindings = KeyBindings()

        for i, mode in enumerate(Mode):
            first_letter = mode.name.lower()[0]

            bindings.add("c-x", first_letter)(self.switch_mode(mode))

        bindings.add("left")(self.previous_mode)
        bindings.add("right")(self.next_mode)

        return bindings

    def switch_mode(self, mode: Mode) -> Callable[[KeyPressEvent], None]:
        def switch(_event: KeyPressEvent) -> None:
            self.mode = mode

        return switch

    def next_mode(self, _event: KeyPressEvent) -> None:
        modes = list(Mode)
        self.mode = modes[(modes.index(self.mode) + 1) % len(modes)]

    def previous_mode(self, _event: KeyPressEvent) -> None:
        modes = list(Mode)
        self.mode = modes[(modes.index(self.mode) - 1) % len(modes)]

    @cached_property
    def session(self) -> PromptSession[str]:
        return PromptSession(
            history=FileHistory(str(HISTORY_PATH)),
            bottom_toolbar=self.bottom_toolbar,
            refresh_interval=0.25,
            rprompt=self.rprompt,
            style=self.session_style,
            key_bindings=self.session_bindings,
        )

    def __post_init__(self) -> None:
        super().__init__()

    def rprompt(self) -> HTML:
        mode_str = "/".join(
            [
                f"<b>{mode.name[0]}{mode.name[1:].lower()}</b>"
                if mode is self.mode
                else mode.name[0]
                for mode in Mode
            ]
        )

        return HTML(f"&lt;{mode_str}&gt;")

    def bottom_toolbar(self) -> str:
        if self.debug:
            return self.debug
        if self.watcher.last_error is not None:
            self.counter = 0
            return f"Error: {self.watcher.last_error}"
        elif self.watcher.running:
            self.counter = (self.counter + 1) % 4
            return "Updating" + ("." * self.counter)
        else:
            self.counter = 0
            return "Up-to-date!"

    def run(self) -> None:
        observer = Observer()
        observer.schedule(self.watcher, ".", recursive=True)
        observer.start()
        try:
            while True:
                line = self.line(self.session.prompt("> "))

                if self.watcher.changed:
                    self.watcher.changed = False

                if not line:
                    continue

                print(self.run_line(line))
        except (EOFError, KeyboardInterrupt):
            print("Goodbye.")
            return
        finally:
            observer.stop()
            observer.join()

    def run_line(self, line: str, mode: Mode | None = None) -> str:
        try:
            return (mode or self.mode)(self.translator, line)
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    def line(self, line: str) -> str:
        self.last_line = line or self.last_line
        return self.last_line


@contextlib.contextmanager
def create_session() -> Generator[ReplSession, None, None]:
    with Translator.new() as translator:
        session = ReplSession(translator, Handler(Compiler(translator)))
        yield session
        session.watcher.join()


def run(command: str = "") -> None:
    with create_session() as session:
        if command:
            print(session.run_line(command))
        else:
            session.run()
