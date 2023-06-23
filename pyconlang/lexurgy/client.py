from dataclasses import dataclass
from functools import cached_property
from subprocess import Popen
from typing import IO

from .domain import (
    AnyLexurgyResponse,
    LexurgyErrorResponse,
    LexurgyRequest,
    LexurgyResponse,
)


@dataclass
class LexurgyClient:
    popen: Popen[str]

    @cached_property
    def stdin(self) -> IO[str]:
        assert self.popen.stdin is not None
        return self.popen.stdin

    @cached_property
    def stdout(self) -> IO[str]:
        assert self.popen.stdout is not None
        return self.popen.stdout

    def write_line(self, line: str) -> None:
        self.stdin.write(f"{line}\n")

    def read_line(self) -> str:
        return self.stdout.readline()

    def send(self, request: LexurgyRequest) -> None:
        self.write_line(request.to_json())

    def receive(self) -> AnyLexurgyResponse:
        line = self.read_line()
        try:
            return LexurgyResponse.from_json(line)
        except:
            return LexurgyErrorResponse.from_json(line)

    def roundtrip(self, request: LexurgyRequest) -> AnyLexurgyResponse:
        self.send(request)
        return self.receive()
