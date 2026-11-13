"""Where the game's files are, whether run from source or packaged (PyInstaller / pygbag)."""

import sys
from pathlib import Path


def game_dir() -> Path:
    """The folder holding assets/ (src/'s parent when run from source)."""
    bundle = getattr(sys, "_MEIPASS", None)  # set by PyInstaller
    if bundle:
        return Path(bundle)
    here = Path(__file__).resolve().parent
    if (here / "assets").is_dir():  # browser build: the modules sit next to assets/
        return here
    return here.parent


def asset(*parts: str) -> Path:
    return game_dir().joinpath("assets", *parts)
