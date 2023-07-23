class PyconlangError(Exception):
    ...


class DoubleTagDefinition(PyconlangError):
    ...


def show_exception(exception: Exception) -> str:
    return f"{type(exception).__name__}: {exception}"
