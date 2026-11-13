import os
import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).parents[2] / "src" / "main.py"


def test_free_play_runs_exits_cleanly_and_writes_a_log(tmp_path) -> None:
    env = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}
    result = subprocess.run(
        [
            sys.executable,
            str(MAIN),
            "--free-play",
            "--max-frames",
            "120",
            "--log-dir",
            str(tmp_path),
        ],
        capture_output=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, result.stderr.decode()
    logs = list(tmp_path.glob("*.md"))
    assert len(logs) == 1
    text = logs[0].read_text()
    assert "Status: **complete**" in text
    assert "## Game 1" in text
