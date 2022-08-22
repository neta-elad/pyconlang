from hashlib import md5
from pathlib import Path


def checksum(path: Path) -> bytes:
    return md5(path.read_bytes()).digest()
