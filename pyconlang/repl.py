from prompt_toolkit import PromptSession

from .lexurgy import evolve_word


def run() -> None:
    session: PromptSession[str] = PromptSession()
    try:
        while True:
            line = session.prompt("> ")

            if not line:
                continue

            print(evolve_word(line.strip()))
    except (EOFError, KeyboardInterrupt):
        print("Goodbye.")
        return
