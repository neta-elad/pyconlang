from cmd import Cmd
from dataclasses import dataclass, field

from prompt_toolkit import PromptSession
from unidecode import unidecode

from .lexicon import Lexicon, parse_lexicon_file


@dataclass
class ReplSession(Cmd):
    lexicon: Lexicon = field(default_factory=parse_lexicon_file)
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
        print(" ".join(form.modern for form in self.lexicon.evolve_string(line)))

    def do_phonetic(self, line: str) -> None:
        print(" ".join(form.phonetic for form in self.lexicon.evolve_string(line)))

    def do_p(self, line: str) -> None:
        self.do_phonetic(line)

    def do_simple(self, line: str) -> None:
        print(
            " ".join(
                unidecode(form.modern) for form in self.lexicon.evolve_string(line)
            )
        )

    def do_s(self, line: str) -> None:
        self.do_simple(line)


def run() -> None:
    ReplSession().run()
