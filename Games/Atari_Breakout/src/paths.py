"""Where the game's files are, whether run from source or packaged (PyInstaller / pygbag)."""

import sys
from pathlib import Path


def game_dir() -> Path:
    """The folder holding src/ and assets/ (or the packaged equivalent)."""
    bundle = getattr(sys, "_MEIPASS", None)  # set by PyInstaller
    if bundle:
        return Path(bundle)
    return Path(__file__).resolve().parents[1]


def asset(*parts: str) -> Path:
    return game_dir().joinpath("assets", *parts)
