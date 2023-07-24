from collections.abc import Generator
from contextlib import contextmanager
from typing import ContextManager, TypeVar

_T = TypeVar("_T", covariant=True)


class PyconlangError(Exception):
    ...


class DoubleTagDefinition(PyconlangError):
    ...


def show_exception(exception: Exception) -> str:
    return f"{type(exception).__name__}: {exception}"


@contextmanager
def pass_exception(manager: ContextManager[_T]) -> Generator[_T, None, None]:
    exception: Exception | None = None
    with manager as context:
        try:
            yield context
        except Exception as e:
            exception = e

    if exception is not None:
        raise exception
