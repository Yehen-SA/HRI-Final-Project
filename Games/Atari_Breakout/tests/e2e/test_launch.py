import os
import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).parents[2] / "src" / "main.py"


def test_game_runs_and_exits_cleanly() -> None:
    env = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}
    result = subprocess.run(
        [sys.executable, str(MAIN), "--max-frames", "120"], capture_output=True, timeout=60, env=env
    )
    assert result.returncode == 0, result.stderr.decode()
