from pathlib import Path

__version__ = "0.0.1"

PYCONLANG_DIRECTORY = ".pyconlang"
PYCONLANG_PATH = Path(PYCONLANG_DIRECTORY)
SRC_PATH = Path("src")
ASSETS_PATH = Path("assets")
SRC_GLOB = (SRC_PATH, "**/*.out.md")
CHANGES_PATH = SRC_PATH / "changes.lsc"
CHANGES_GLOB = (SRC_PATH, "**/*.lsc")
LEXICON_PATH = SRC_PATH / "lexicon.pycl"
LEXICON_GLOB = (SRC_PATH, "**/*.pycl")
