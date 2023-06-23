from pathlib import Path
from subprocess import PIPE, Popen

from .. import PYCONLANG_PATH
from ..assets import LEXURGY_VERSION
from .client import LexurgyClient

LEXURGY_PATH = PYCONLANG_PATH / f"lexurgy-{LEXURGY_VERSION}" / "bin" / "lexurgy"
CHANGES_PATH = Path("changes.lsc")


def client() -> LexurgyClient:
    args = [
        "sh",
        str(LEXURGY_PATH),
        "server",
        str(CHANGES_PATH),
    ]
    return LexurgyClient(Popen(args, stdin=PIPE, stdout=PIPE, text=True, bufsize=1))
