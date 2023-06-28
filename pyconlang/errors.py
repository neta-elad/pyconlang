from pyparsing import ParseBaseException


class PyconlangError(Exception):
    ...


class AffixDefinitionMissingForm(PyconlangError):
    ...


class AffixDefinitionMissingVar(PyconlangError):
    ...


class LexurgyClientError(PyconlangError):
    ...


class LexurgyResponseMissingType(LexurgyClientError):
    ...


class LexurgyResponseBadType(LexurgyClientError):
    ...


def show_exception(exception: Exception) -> str:
    match exception:
        case ParseBaseException():
            return exception.explain(depth=0)
        case _:
            return f"{type(exception).__name__}: {exception}"
