from functools import cached_property
from subprocess import PIPE, Popen
from threading import RLock
from typing import IO

from .. import CHANGES_GLOB, CHANGES_PATH, PYCONLANG_PATH
from ..assets import LEXURGY_VERSION
from ..cache import path_cached_property
from .domain import AnyLexurgyResponse, LexurgyRequest, parse_response

LEXURGY_PATH = PYCONLANG_PATH / f"lexurgy-{LEXURGY_VERSION}" / "bin" / "lexurgy"


class LexurgyClient:
    @path_cached_property(CHANGES_PATH, CHANGES_GLOB)
    def popen(self) -> Popen[str]:
        args = [
            "sh",
            str(LEXURGY_PATH),
            "server",
            str(CHANGES_PATH),
        ]
        return Popen(args, stdin=PIPE, stdout=PIPE, text=True, bufsize=1)

    @cached_property
    def lock(self) -> RLock:
        return RLock()

    @property
    def stdin(self) -> IO[str]:
        assert self.popen.stdin is not None
        return self.popen.stdin

    @property
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
        return parse_response(self.read_line())

    def roundtrip(self, request: LexurgyRequest) -> AnyLexurgyResponse:
        self.lock.acquire()
        self.send(request)
        response = self.receive()
        self.lock.release()
        return response
