import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).parents[2] / "src" / "main.py"


def test_game_starts_and_exits_cleanly() -> None:
    result = subprocess.run([sys.executable, str(MAIN)], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
