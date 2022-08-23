from wcwidth import wcswidth

PRIMARY_STRESS = "\u02c8"


def remove_primary_stress(word: str) -> str:
    return word.replace(PRIMARY_STRESS, "")


def length(string: str) -> int:
    return wcswidth(string)


def center(string: str, width: int, fill_char: str = " ") -> str:
    diff = max(0, width - length(string))
    add_left = int(diff / 2)
    add_right = int((diff + 1) / 2)

    return fill_char * add_left + string + fill_char * add_right
