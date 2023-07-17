from ..errors import PyconlangError


class LexurgyClientError(PyconlangError):
    ...


class LexurgyResponseMissingType(LexurgyClientError):
    ...


class LexurgyResponseBadType(LexurgyClientError):
    ...
