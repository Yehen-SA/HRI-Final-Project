import json
import re
from datetime import datetime

from engine import Game
from robot_strategies import Strategy
from session_log import Answer, SessionLog
from stats import RoundStats

NOW = datetime(2026, 11, 13, 14, 30, 0)


def json_block(text: str) -> dict:
    match = re.search(r"```json\n(.*)\n```", text, re.S)
    assert match, "no JSON block"
    return json.loads(match.group(1))


def play_round(seconds: float = 1) -> RoundStats:
    stats = RoundStats()
    game = Game(round_seconds=seconds, robot_strategy=Strategy.GOOD, rules=[], listeners=[stats])
    while not game.over:
        game.update(launch_pressed=True)
    return stats


def test_full_log_has_every_section_and_valid_json(tmp_path) -> None:
    log = SessionLog.create("P07", tmp_path, now=NOW)
    log.write_participant({"score_mode": "shared", "robot_order": ["BAD", "GOOD"]})
    log.write_settings()
    log.write_answers("Stage 1: pre-game questions", [Answer("age", "Your age?", 22)], key="pre")
    log.write_round({"title": "Round 1: robot BAD", "robot": "BAD"}, play_round())
    log.finish("complete")

    text = log.path.read_text()
    assert log.path.name == "2026-11-13_143000_P07.md"
    for heading in (
        "## Participant and conditions",
        "## Settings",
        "## Stage 1: pre-game",
        "## Round 1: robot BAD",
        "## Session end",
        "## Data (JSON)",
    ):
        assert heading in text
    data = json_block(text)
    assert data["status"] == "complete"
    assert data["participant"]["score_mode"] == "shared"
    assert data["answers"]["pre"] == {"age": 22}
    assert data["rounds"][0]["end_reason"] == "timer"
    assert set(data["rounds"][0]["players"]) == {"human", "robot"}


def test_never_overwrites_an_existing_log(tmp_path) -> None:
    first = SessionLog.create("P07", tmp_path, now=NOW)
    first.finish()
    second = SessionLog.create("P07", tmp_path, now=NOW)
    second.finish()
    assert first.path != second.path
    assert second.path.name == "2026-11-13_143000_P07_2.md"
    assert "Status: **complete**" in first.path.read_text()


def test_sections_are_on_disk_before_finish(tmp_path) -> None:
    log = SessionLog.create("P08", tmp_path, now=NOW)
    log.write_answers("Stage 1", [Answer("q", "Question?", "yes")])
    assert "Question?" in log.path.read_text()  # survives a crash from here on
    log.finish("aborted")
    assert json_block(log.path.read_text())["status"] == "aborted"


def test_answers_with_pipes_and_newlines_keep_the_table_intact(tmp_path) -> None:
    log = SessionLog.create("P09", tmp_path, now=NOW)
    log.write_answers("Stage 3", [Answer("c", "Comments?", "a | b\nc")])
    log.finish()
    row = next(line for line in log.path.read_text().splitlines() if line.startswith("| c |"))
    assert len(re.findall(r"(?<!\\)\|", row)) == 4  # 3 cells; the answer's pipe is escaped
    assert row.endswith("a \\| b c |")
