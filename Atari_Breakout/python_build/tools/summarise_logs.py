"""Summarise participant logs for the report and the analysis.

Run from the game folder (python_build):

    uv run tools/summarise_logs.py [--logs DIR] [--csv FILE]

Reads every log in Data/participant_logs/ (at the repo root; see Data/README.md), then:

- prints, per participant, possession, steals, rescues and scores, plus a LaTeX row for the
  report's data table (Appendix B: possession and score) to paste into Overleaf. Interviewer
  and "Started" are filled in by hand there.
- writes Data/results.csv: one row per participant per round (practice included) with every
  measure the game records, the round's questionnaire answers, and the pre-game answers.

Each log's data comes from the JSON block at its end. A log without one (the game crashed
before finishing) is reported and skipped.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DEFAULT_LOGS = REPO / "Data" / "participant_logs"
DEFAULT_CSV = REPO / "Data" / "results.csv"

JSON_BLOCK = re.compile(r"```json\n(.*)\n```", re.S)


def load(path: Path) -> dict[str, Any] | None:
    match = JSON_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        return None
    return json.loads(match.group(1))


def fraction(made: int, chances: int) -> str:
    """Unsimplified, e.g. 2/39 (not 0.051)."""
    return f"{made}/{chances}"


def table_values(round_: dict[str, Any]) -> dict[str, str]:
    """The data-table cells for one round."""
    h, r = round_["players"]["human"], round_["players"]["robot"]
    return {
        "possession": f"{round(h['possession_s'])}:{round(r['possession_s'])}",
        "steals_h": fraction(h["steals_made"], h["steal_chances"]),
        "steals_r": fraction(r["steals_made"], r["steal_chances"]),
        "rescues_h": fraction(h["rescues_made"], h["rescue_chances"]),
        "rescues_r": fraction(r["rescues_made"], r["rescue_chances"]),
        "score": f"{h['score']}:{r['score']}:{round_['team_score']}",
    }


def latex_row(pid: str, score_mode: str, position: int, round_: dict[str, Any]) -> str:
    """A row for the report's data table: ID, score structure, robot order, Started,
    Interviewer (both filled in by hand), possession and score."""
    v = table_values(round_)
    order = f"{'1st' if position == 1 else '2nd'}: {round_['robot'].capitalize()}"
    if position == 1:
        lead = f"{pid} & {score_mode.capitalize()} & {order} & $\\square$ & "
    else:
        lead = f" & & {order} & & "
    possession = v["possession"].replace(":", r"\,:\,")
    score = v["score"].replace(":", r"\,:\,")
    return f"{lead}& {possession} & {score} \\\\"


def csv_rows(path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    """One CSV row per round, with everything flattened into columns."""
    conditions = data.get("participant", {})
    answers = data.get("answers", {})
    rows = []
    for round_ in data.get("rounds", []):
        row: dict[str, Any] = {
            "participant_id": data["participant_id"],
            "log_file": path.name,
            "status": data["status"],
            "platform": data["platform"],
            "started": data["started"],
            "game_version": data["game_version"],
            "score_mode": conditions.get("score_mode"),
            "robot_order": ",".join(conditions.get("robot_order", [])),
            "assigned_by": conditions.get("assigned_by"),
        }
        for key, value in round_.items():
            if key in ("players", "timeline", "title"):
                continue
            row[key] = json.dumps(value) if isinstance(value, dict | list) else value
        for player, stats in round_["players"].items():
            for key, value in stats.items():
                row[f"{player}_{key}"] = json.dumps(value) if isinstance(value, dict) else value
        number = round_.get("round_number")
        for qid, answer in answers.get(f"post_round_{number}", {}).items():
            row[f"post_{qid}"] = json.dumps(answer) if isinstance(answer, list) else answer
        for qid, answer in answers.get("pre", {}).items():
            row[f"pre_{qid}"] = answer
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOGS, help="folder of .md logs")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="CSV file to write")
    args = parser.parse_args()

    paths = sorted(args.logs.glob("*.md"))
    if not paths:
        print(f"No logs in {args.logs}. Put participants' .md log files there.")
        return 1

    all_rows: list[dict[str, Any]] = []
    seen: dict[str, list[str]] = {}
    for path in paths:
        data = load(path)
        if data is None:
            print(f"!! {path.name}: no data block (the game didn't finish writing it); skipped\n")
            continue
        pid = data["participant_id"]
        seen.setdefault(pid, []).append(path.name)
        mode = data.get("participant", {}).get("score_mode", "?")
        print(f"{pid}  ({mode} score, {data['status']}, {data['started']}, {path.name})")
        main_rounds = [r for r in data.get("rounds", []) if r.get("round_kind") == "main"]
        for position, round_ in enumerate(main_rounds, start=1):
            v = table_values(round_)
            print(
                f"  {position}. {round_['robot']:<4} ({round_.get('robot_name', '')})  "
                f"possession {v['possession']}  steals H {v['steals_h']} R {v['steals_r']}  "
                f"rescues H {v['rescues_h']} R {v['rescues_r']}  score {v['score']}"
            )
        for position, round_ in enumerate(main_rounds, start=1):
            print("  " + latex_row(pid, mode, position, round_))
        print()
        all_rows.extend(csv_rows(path, data))

    for pid, files in seen.items():
        if len(files) > 1:
            print(f"!! {pid} has {len(files)} logs ({', '.join(files)}): check which to use")

    columns: list[str] = []
    for row in all_rows:
        columns += [c for c in row if c not in columns]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Wrote {len(all_rows)} rows ({len(columns)} columns) to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
