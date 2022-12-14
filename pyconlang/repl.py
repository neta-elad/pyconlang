from cmd import Cmd
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Callable, List, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from . import PYCONLANG_PATH
from .errors import show_exception
from .evolve.types import Evolved
from .translate import Translator
from .types import Describable
from .unicode import center, length

HISTORY_PATH = PYCONLANG_PATH / "repl.history"


def _default_prompt_session() -> PromptSession[str]:
    return PromptSession(history=FileHistory(str(HISTORY_PATH)))


def _show_lookup_records(records: List[Tuple[Describable, str]]) -> str:
    return "\n".join(
        _show_lookup_record(record, description) for record, description in records
    )


def _show_lookup_record(record: Describable, description: str) -> str:
    return f"{record}: {description}"


class Handler(PatternMatchingEventHandler):
    changed: bool

    def __init__(self) -> None:
        super().__init__(["changes.lsc", "lexicon.txt"])
        self.changed = False

    def on_any_event(self, event: FileSystemEvent) -> None:
        self.changed = True


@dataclass
class ReplSession(Cmd):
    translator: Translator = field(default_factory=Translator)
    session: PromptSession[str] = field(default_factory=_default_prompt_session)
    watcher: Handler = field(default_factory=Handler)
    last_line: str = field(default="")

    def __post_init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        observer = Observer()
        observer.schedule(self.watcher, ".")
        observer.start()
        try:
            while True:
                line = self.session.prompt("> ")

                if self.watcher.changed:
                    self.watcher.changed = False
                    if not self.translator.validate_cache():
                        print("Detected changes, reloading.")

                if not line:
                    continue

                self.run_command(line)
        except (EOFError, KeyboardInterrupt):
            print("Goodbye.")
            return
        finally:
            self.translator.save()
            observer.stop()
            observer.join()

    def line(self, line: str) -> str:
        self.last_line = line or self.last_line
        return self.last_line

    def run_command(self, line: str) -> None:
        try:
            self.onecmd(line)
        except Exception as e:
            print(show_exception(e))

    def translate(
        self, line: str, getter: Callable[[Evolved], str] = attrgetter("modern")
    ) -> None:
        print(
            " ".join(
                getter(form) for form in self.translator.evolve_string(self.line(line))
            )
        )

    def default(
        self,
        line: str,
    ) -> None:
        self.translate(line)

    def do_default(self, line: str) -> None:
        """
        Translates a sentence using the lexicon and sound changes.
        Can also be used without prefixing the command.
        """
        return self.default(line)

    def do_d(self, line: str) -> None:
        """
        See default.
        """
        return self.do_default(line)

    def do_phonetic(self, line: str) -> None:
        """
        Returns the phonetic forms of the translated sentence.
        """
        self.translate(line, attrgetter("phonetic"))

    def do_p(self, line: str) -> None:
        """
        See phonetic.
        """
        self.do_phonetic(line)

    def do_simple(self, line: str) -> None:
        """
        Simplifies the forms of the translated sentence into basic ascii.
        """
        self.translate(line, attrgetter("simple"))

    def do_s(self, line: str) -> None:
        """
        See simple.
        """
        self.do_simple(line)

    def do_gloss(self, line: str) -> None:
        """
        Translates and glosses the translation.
        """
        gloss = [
            (evolved.modern, str(form))
            for evolved, form in self.translator.gloss_string(self.line(line))
        ]

        print(
            " ".join(center(pair[0], 2 + max(map(length, pair)), " ") for pair in gloss)
        )
        print(
            " ".join(center(pair[1], 2 + max(map(length, pair)), " ") for pair in gloss)
        )

    def do_g(self, line: str) -> None:
        """
        See gloss.
        """
        return self.do_gloss(line)

    def do_lookup(self, line: str) -> None:
        """
        Breaks down compound forms and looks them up in the lexicon.
        """
        result = self.translator.lookup_string(self.line(line))

        if len(result) == 1:
            print(_show_lookup_records(result[0][1]))
        else:
            print(
                "\n\n".join(
                    f"Records for {form}\n{_show_lookup_records(foo)}"
                    for form, foo in result
                )
            )

    def do_lexicon(self, line: str) -> None:
        """
        See lookup.
        """
        return self.do_lookup(line)

    def do_l(self, line: str) -> None:
        """
        See lookup.
        """
        return self.do_lookup(line)

    def do_trace(self, line: str) -> None:
        """
        Traces the sound changes for each individual query sent to Lexurgy.
        """
        for evolved, trace in self.translator.trace_string(self.line(line)):
            for query, lines in trace:
                print(query)
                for trace_line in lines:
                    print(
                        f"{trace_line.before} => {trace_line.after} ({trace_line.rule})"
                    )

    def do_t(self, line: str) -> None:
        """
        See trace.
        """
        return self.do_trace(line)


def run(command: str = "") -> None:
    session = ReplSession()

    if command:
        session.run_command(command)
    else:
        session.run()
