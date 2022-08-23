from ..errors import PyconlangError


class LexiconError(PyconlangError):
    ...


class MissingCanonical(LexiconError):
    ...


class MissingAffix(LexiconError):
    ...


class MissingTemplate(LexiconError):
    ...


class UnexpectedRecord(LexiconError):
    ...
