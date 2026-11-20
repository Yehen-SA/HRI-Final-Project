"""A whole study session on autoplay, run as the participant would launch it."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).parents[2] / "src" / "main.py"
ENV = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}


def run(tmp_path: Path, *args: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(MAIN), "--log-dir", str(tmp_path), *args],
        capture_output=True,
        timeout=120,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr.decode()
    logs = sorted(tmp_path.glob("*.md"))
    text = logs[-1].read_text()
    match = re.search(r"```json\n(.*)\n```", text, re.S)
    assert match, "log has no JSON block"
    return json.loads(match.group(1))


def test_full_session_writes_a_complete_log(tmp_path) -> None:
    data = run(tmp_path, "--autoplay", "--pid", "P03", "--round-seconds", "2")
    assert data["status"] == "complete"
    assert data["participant"] == {
        "score_mode": "shared",
        "robot_order": ["GOOD", "BAD"],
        "assigned_by": "id number",
        "robot_names": ["Nova", "Pip"],
    }
    assert set(data["answers"]) == {"pre", "post_round_1", "post_round_2"}  # no final stage
    post = data["answers"]["post_round_1"]
    assert "valuable_contribution" in post and "robot_share_estimate" in post  # shared only
    assert "competing" not in post  # split only
    kinds = [(r["round_kind"], r["robot"], r.get("robot_name")) for r in data["rounds"]]
    assert kinds == [("practice", "none", None), ("main", "GOOD", "Nova"), ("main", "BAD", "Pip")]


def test_rerun_makes_a_second_log(tmp_path) -> None:
    for _ in range(2):
        run(tmp_path, "--autoplay", "--pid", "P04", "--round-seconds", "1")
    assert len(list(tmp_path.glob("*.md"))) == 2


def test_quitting_early_leaves_an_aborted_partial_log(tmp_path) -> None:
    data = run(
        tmp_path, "--autoplay", "--pid", "P05", "--round-seconds", "30", "--max-frames", "200"
    )
    assert data["status"] == "aborted"
    assert data["rounds"][-1]["end_reason"] == "quit"
