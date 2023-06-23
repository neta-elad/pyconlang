from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class TraceLine:
    rule: str
    word: str
    before: str
    after: str

    def set_word(self, new_word: str) -> "TraceLine":
        return TraceLine(self.rule, new_word, self.before, self.after)
