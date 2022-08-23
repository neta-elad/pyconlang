from cmd import Cmd
from dataclasses import dataclass, field

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from unidecode import unidecode
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from . import PYCONLANG_PATH
from .translate import Translator

HISTORY_PATH = PYCONLANG_PATH / "repl.history"


def _default_prompt_session() -> PromptSession[str]:
    return PromptSession(history=FileHistory(str(HISTORY_PATH)))


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

    def run_command(self, line: str) -> None:
        try:
            self.onecmd(line)
        except Exception as e:
            print(f"Bad command: {repr(e)}")

    def default(self, line: str) -> None:
        print(" ".join(form.modern for form in self.translator.evolve_string(line)))

    def do_phonetic(self, line: str) -> None:
        print(" ".join(form.phonetic for form in self.translator.evolve_string(line)))

    def do_p(self, line: str) -> None:
        self.do_phonetic(line)

    def do_simple(self, line: str) -> None:
        print(
            " ".join(
                unidecode(form.modern) for form in self.translator.evolve_string(line)
            )
        )

    def do_s(self, line: str) -> None:
        self.do_simple(line)


def run(command: str = "") -> None:
    session = ReplSession()

    if command:
        session.run_command(command)
    else:
        session.run()
