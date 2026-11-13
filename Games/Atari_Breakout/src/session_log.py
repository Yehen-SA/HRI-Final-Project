"""The session log: one Markdown file per run, in a `logs/` folder.

- Every run gets a new file named `<date>_<time>_<participant>.md`. An existing file is never
  overwritten.
- Each section is written and flushed as soon as it's ready, so an early quit or crash still
  leaves everything up to that point.
- The file ends with a fenced `json` block holding the same data, for analysis scripts.

Typical use:

    log = SessionLog.create(participant_id="P07")
    log.write_participant({"score_mode": "shared", ...})
    log.write_settings()
    log.write_answers("Stage 1: pre-game questions", answers)
    log.write_round(round_info, stats)
    log.finish("complete")
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

import config
import robot_strategies
import rules
from stats import ROWS, RoundStats

LOG_FORMAT_VERSION = 1


def platform_name() -> str:
    """ "web" in the browser build, "exe" in the packaged build, otherwise "desktop"."""
    if sys.platform == "emscripten":
        return "web"
    if getattr(sys, "frozen", False):
        return "exe"
    return "desktop"


def default_log_dir() -> Path:
    """`logs/` next to the exe when packaged, otherwise in the game folder."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "logs"
    return Path(__file__).resolve().parents[1] / "logs"


def new_log_path(log_dir: Path, participant_id: str, now: datetime) -> Path:
    """A file name that doesn't exist yet: adds _2, _3... if needed."""
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in participant_id) or "unknown"
    stem = f"{now:%Y-%m-%d_%H%M%S}_{safe_id}"
    path = log_dir / f"{stem}.md"
    n = 2
    while path.exists():
        path = log_dir / f"{stem}_{n}.md"
        n += 1
    return path


def settings_snapshot() -> dict[str, Any]:
    """Config values, enabled rules and robot strategy tuning, as plain data."""
    cfg = {k: getattr(config, k) for k in dir(config) if k.isupper()}
    strategies = {
        s.name: {k: getattr(cls, k) for k in dir(cls) if k.isupper() and not k.startswith("_")}
        for s, cls in robot_strategies.STRATEGIES.items()
    }
    return {
        "config": cfg,
        "rules": [{"name": r.name, "enabled": r.enabled, **r.settings()} for r in rules.RULES],
        "robot_strategies": strategies,
    }


def _cell(value: Any) -> str:
    """Make a value safe for a Markdown table cell."""
    if value is None:
        return "–"
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


@dataclass
class Answer:
    question_id: str
    question: str
    answer: Any


class SessionLog:
    def __init__(self, path: Path, file: TextIO, participant_id: str, started: datetime) -> None:
        self.path = path
        self._file = file
        self.finished = False
        self.data: dict[str, Any] = {
            "log_format_version": LOG_FORMAT_VERSION,
            "game_version": config.GAME_VERSION,
            "platform": platform_name(),
            "participant_id": participant_id,
            "started": started.isoformat(timespec="seconds"),
            "finished": None,
            "status": "in progress",
            "participant": {},
            "settings": {},
            "answers": {},
            "rounds": [],
        }

    @classmethod
    def create(
        cls, participant_id: str, log_dir: Path | None = None, now: datetime | None = None
    ) -> "SessionLog":
        """Start a new log file (never overwrites an existing one)."""
        log_dir = log_dir or default_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        now = now or datetime.now()
        path = new_log_path(log_dir, participant_id, now)
        file = path.open("x", encoding="utf-8")  # "x": fail rather than overwrite
        log = cls(path, file, participant_id, now)
        d = log.data
        log._write(
            f"# HRI Breakout session log\n\n"
            f"- Participant: **{participant_id}**\n"
            f"- Started: {d['started']}\n"
            f"- Platform: {d['platform']}\n"
            f"- Game version: {d['game_version']}\n"
            f"- Log format version: {LOG_FORMAT_VERSION}\n\n"
        )
        return log

    def _write(self, text: str) -> None:
        self._file.write(text)
        self._file.flush()

    # --- Sections ---

    def write_participant(self, conditions: dict[str, Any]) -> None:
        """The independent variables for this participant (score mode, robot order...)."""
        self.data["participant"] = conditions
        rows = [[k, v] for k, v in conditions.items()]
        self._write("## Participant and conditions\n\n" + _table(["Setting", "Value"], rows) + "\n")

    def write_settings(self) -> None:
        snap = settings_snapshot()
        self.data["settings"] = snap
        text = "## Settings\n\n### Optional rules\n\n"
        text += _table(
            ["Rule", "Enabled", "Settings"],
            [
                [
                    r["name"],
                    "yes" if r["enabled"] else "no",
                    ", ".join(f"{k}={v}" for k, v in r.items() if k not in ("name", "enabled")),
                ]
                for r in snap["rules"]
            ],
        )
        text += "\n### Robot strategies\n\n"
        text += _table(
            ["Strategy", "Tuning"],
            [
                [name, ", ".join(f"{k}={v}" for k, v in t.items())]
                for name, t in snap["robot_strategies"].items()
            ],
        )
        text += "\n<details><summary>All config values</summary>\n\n"
        text += _table(["Name", "Value"], [[k, v] for k, v in snap["config"].items()])
        text += "\n</details>\n\n"
        self._write(text)

    def write_answers(self, title: str, answers: list[Answer], key: str | None = None) -> None:
        """Survey answers as a table. `key` names them in the JSON (defaults to the title)."""
        self.data["answers"][key or title] = {a.question_id: a.answer for a in answers}
        rows = [[a.question_id, a.question, a.answer] for a in answers]
        self._write(f"## {title}\n\n" + _table(["ID", "Question", "Answer"], rows) + "\n")

    def write_round(self, info: dict[str, Any], stats: RoundStats) -> dict[str, Any]:
        """One round: its settings, the per-player stats table, and the event timeline."""
        summary = stats.summary()
        entry = {**info, **summary}
        if config.LOG_TIMELINE:
            entry["timeline"] = stats.timeline
        self.data["rounds"].append(entry)

        number = len(self.data["rounds"])
        title = info.get("title", f"Round {number}")
        text = f"## {title}\n\n"
        round_rows = [[k, v] for k, v in info.items() if k != "title"]
        round_rows += [
            ["Duration (s)", summary["duration_s"]],
            ["End reason", summary["end_reason"]],
            ["Team score", summary["team_score"]],
            ["Robot's share of the score", summary["robot_share_of_score"]],
            ["Bricks broken / left", f"{summary['bricks_broken']} / {summary['bricks_left']}"],
            ["Paddles overlapping (s)", summary["paddles_overlapping_s"]],
            ["Most balls in play", summary["max_balls_in_play"]],
        ]
        text += _table(["Round", "Value"], round_rows) + "\n"
        players = summary["players"]
        text += _table(
            ["Measure", "Human", "Robot"],
            [[label, players["human"][key], players["robot"][key]] for key, label in ROWS],
        )
        reasons = sorted({r for p in players.values() for r in p["points_by_reason"]} - {"bricks"})
        if reasons:
            text += "\nPoints by reason:\n\n" + _table(
                ["Reason", "Human", "Robot"],
                [
                    [
                        r,
                        players["human"]["points_by_reason"].get(r, 0),
                        players["robot"]["points_by_reason"].get(r, 0),
                    ]
                    for r in reasons
                ],
            )
        if config.LOG_TIMELINE and stats.timeline:
            text += f"\n<details><summary>Timeline ({len(stats.timeline)} events)</summary>\n\n"
            text += _table(
                ["Time (s)", "Event", "Player", "Detail"],
                [[e["t"], e["event"], e["player"], e["detail"]] for e in stats.timeline],
            )
            text += "\n</details>\n"
        self._write(text + "\n")
        return entry

    def finish(self, status: str = "complete") -> None:
        """Close the log: "complete" or "aborted". Safe to call twice."""
        if self.finished:
            return
        self.finished = True
        self.data["status"] = status
        self.data["finished"] = datetime.now().isoformat(timespec="seconds")
        self._write(
            f"## Session end\n\n- Status: **{status}**\n- Finished: {self.data['finished']}\n\n"
            "## Data (JSON)\n\n```json\n" + json.dumps(self.data, indent=2, default=str) + "\n```\n"
        )
        self._file.close()
