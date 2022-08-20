PRIMARY_STRESS = "\u02c8"


def remove_primary_stress(word: str) -> str:
    return word.replace(PRIMARY_STRESS, "")
