import shutil
from importlib.resources import files
from pathlib import Path

import click

from . import PYCONLANG_PATH
from .assets import LEXURGY_VERSION
from .book import compile_book
from .book import watch as watch_book
from .metadata import Metadata
from .repl import run as run_repl


@click.group
def run() -> None:
    pass


@run.command
def reset() -> None:
    try:
        shutil.rmtree(PYCONLANG_PATH)
    except FileNotFoundError:
        return


@run.command
@click.argument(
    "directory", type=click.Path(file_okay=False, path_type=Path), default="."
)
@click.option(
    "-n", "--name", default="NewLang", help="Name of the scope (can be changed later)"
)
@click.option(
    "-a",
    "--author",
    default="Author Name",
    help="Name of the author (can be changed later)",
)
@click.option(
    "-o", "--overwrite", is_flag=True, default=False, help="Overwrite user files"
)
@click.option(
    "-l", "--lexurgy-only", is_flag=True, default=False, help="Only install Lexurgy"
)
def init(
    directory: Path, name: str, author: str, overwrite: bool, lexurgy_only: bool
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    lexurgy_zip = str(
        files("pyconlang.assets").joinpath(f"lexurgy-{LEXURGY_VERSION}.zip")
    )
    shutil.unpack_archive(lexurgy_zip, directory / PYCONLANG_PATH)

    if lexurgy_only:
        return

    for file in files("pyconlang.assets.template").iterdir():
        target = directory / file.name

        if not file.is_file():
            continue

        if not target.exists() or overwrite:
            shutil.copyfile(str(file), target)

    Metadata(name=name, author=author).save(overwrite=overwrite)


@run.command
@click.argument("command", nargs=-1)
def repl(command: list[str]) -> None:
    run_repl(" ".join(command))


@run.group
def book() -> None:
    pass


book.command(name="watch")(watch_book)
book.command(name="compile")(compile_book)
