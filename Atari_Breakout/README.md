# Atari Breakout (HRI study game)

One game, three ways to run it. All code lives in `python_build/`; the other two folders are
generated from it, and each is a complete package on its own.

| Folder | What it is | Who it's for | How to make it |
|---|---|---|---|
| [python_build/](python_build/) | The source, run with Python and uv | Our own devices; development | `cd python_build && uv run src/main.py` |
| [html_build/](html_build/) | Browser version (pygbag) | Subjects on their own computer, any OS, via a link | `cd python_build && uv run ../build_html.py`, then host it |
| [exe_build/](exe_build/) | Windows .exe (PyInstaller) | Subjects on Windows, without internet during play | `build_exe.ps1`, run on Windows |

All three write the same Markdown results log. Python and the exe save it to a `logs/` folder;
the browser downloads it.

Rebuild `html_build/` and `exe_build/` after any change to `python_build/`. Build outputs aren't
kept in git, only their READMEs.

For how the game works and where to change things, see
[python_build/README.md](python_build/README.md).
