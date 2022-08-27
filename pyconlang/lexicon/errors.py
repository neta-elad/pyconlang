from ..errors import PyconlangError


class LexiconError(PyconlangError):
    ...


class MissingLexeme(LexiconError):
    ...


class MissingAffix(LexiconError):
    ...


class MissingTemplate(LexiconError):
    ...


class UnexpectedRecord(LexiconError):
    ...
