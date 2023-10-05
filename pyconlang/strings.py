from wcwidth import wcswidth

from .config import config

PRIMARY_STRESS = "\u02c8"
SYLLABLE_BREAK = "."


def remove_primary_stress(word: str) -> str:
    return word.replace(PRIMARY_STRESS, "")


def length(string: str) -> int:
    return wcswidth(string)


def center(string: str, width: int, fill_char: str = " ") -> str:
    diff = max(0, width - length(string))
    add_left = int(diff / 2)
    add_right = int((diff + 1) / 2)

    return fill_char * add_left + string + fill_char * add_right


def combine(head: str, tail: str, syllable_break: str | None = None) -> str:
    if syllable_break is None:
        syllable_break = default_syllable_break()

    return head + syllable_break + tail


def default_syllable_break() -> str:
    if config().syllables:
        return SYLLABLE_BREAK
    else:
        return ""


def remove_syllable_break(word: str) -> str:
    return word.replace(SYLLABLE_BREAK, "")
