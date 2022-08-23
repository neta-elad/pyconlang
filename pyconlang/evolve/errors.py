from ..errors import PyconlangError


class EvolveError(PyconlangError):
    ...


class LexurgyError(EvolveError):
    ...


class BadAffixation(EvolveError):
    ...
