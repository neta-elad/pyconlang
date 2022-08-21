from cmd import Cmd
from dataclasses import dataclass, field

from prompt_toolkit import PromptSession
from unidecode import unidecode

from .translate import Translator


@dataclass
class ReplSession(Cmd):
    translator: Translator = field(default_factory=Translator)
    session: PromptSession[str] = field(default_factory=PromptSession)

    def run(self) -> None:
        try:
            while True:
                line = self.session.prompt("> ")

                if not line:
                    continue

                self.onecmd(line)
        except (EOFError, KeyboardInterrupt):
            print("Goodbye.")
            return

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
        session.onecmd(command)
    else:
        session.run()
