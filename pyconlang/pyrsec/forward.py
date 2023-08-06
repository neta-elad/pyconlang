from dataclasses import dataclass, field
from typing import Callable, TypeVar, cast

from .core import Parser, PyrsecError, Value

_U = TypeVar("_U", covariant=True)
_I = TypeVar("_I", contravariant=True)


@dataclass
class ForwardParser(Parser[_I, _U]):
    parser: Parser[_I, _U] | None = field(default=None)

    def __call__(self, text: _I, index: int) -> Value[_U]:
        if self.parser is None:
            raise PyrsecError(text, index, "Using uninitialized ForwardParser")
        return self.parser(text, index)


def fix(fun: Callable[[Parser[_I, _U]], Parser[_I, _U]]) -> Parser[_I, _U]:
    forward = cast(ForwardParser[_I, _U], ForwardParser())
    forward.parser = fun(forward)
    return forward
