import subprocess
import sys


def test_game_module_runs() -> None:
    result = subprocess.run([sys.executable, "-m", "breakout"], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
