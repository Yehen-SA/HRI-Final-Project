"""Build the browser version into html_build/, using pygbag.

Run from the python_build folder (pygbag is one of its dev dependencies):

    cd python_build
    uv run ../build_html.py

It copies the game (src/ and assets/) into .html_stage/hri_breakout/ in the layout pygbag
expects (main.py at the top, assets/ beside it), builds it, and copies the result into
html_build/. Existing files are overwritten, never deleted.

It also writes html_build_itch.zip (the build files with index.html at the top), ready to
upload to itch.io; see html_build/README.md.

The result must be served over http(s) (e.g. GitHub Pages or itch.io); browsers won't run it
from a double-clicked index.html. To try it locally:

    python -m http.server --directory html_build 8000   then open http://localhost:8000
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "python_build"
STAGE = HERE / ".html_stage" / "hri_breakout"  # folder name = package name in the browser
OUTPUT = HERE / "html_build"
ITCH_ZIP = HERE / "html_build_itch.zip"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "logs")

sys.path.insert(0, str(SOURCE / "src"))
import config  # noqa: E402


def main() -> None:
    STAGE.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE / "src", STAGE, ignore=IGNORE, dirs_exist_ok=True)
    shutil.copytree(SOURCE / "assets", STAGE / "assets", ignore=IGNORE, dirs_exist_ok=True)
    print(f"Staged the game in {STAGE}")

    subprocess.run(
        [
            sys.executable, "-m", "pygbag", "--build",
            "--title", "HRI Breakout",
            "--width", str(config.SCREEN_WIDTH),
            "--height", str(config.SCREEN_HEIGHT),
            "--ume_block", "1",  # wait for a click before starting (browsers need it for sound)
            str(STAGE),
        ],
        check=True,
    )

    built = STAGE / "build" / "web"
    OUTPUT.mkdir(exist_ok=True)
    shutil.copytree(built, OUTPUT, dirs_exist_ok=True)
    print(f"\nBrowser build ready in {OUTPUT}")

    # Zip of this build's files only (not older leftovers in html_build/), for itch.io.
    with zipfile.ZipFile(ITCH_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(built.iterdir()):
            if path.is_file():
                zf.write(path, path.name)
    print(f"itch.io upload: {ITCH_ZIP}")
    print("Try it: python -m http.server --directory html_build 8000, then open http://127.0.0.1:8000")


if __name__ == "__main__":
    main()
