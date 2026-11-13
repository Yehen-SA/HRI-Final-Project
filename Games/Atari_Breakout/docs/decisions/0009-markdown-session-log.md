# 0009: One Markdown log per session, with a JSON block

Status: accepted

## Context

We need each run's settings, independent variables, scores, behaviour measures and survey
answers in one place. It should be readable by eye, easy to send back (for subjects playing on
their own computers), and easy to load for analysis. Earlier plans used a database; the team
chose a file instead.

## Decision

- `session_log.py` writes `logs/<date>_<time>_<participant>.md`. It opens with mode `"x"`, so
  an existing file is never overwritten; a clashing name gets `_2`, `_3`.
- Sections are written and flushed as they happen: participant and conditions, settings
  (config, rules, robot tuning), survey answers, one section per round, then session end.
- Each round has a `Measure | Human | Robot` table (`stats.py`), points by reason, and a
  collapsible event timeline (`LOG_TIMELINE`).
- The file ends with a fenced `json` block holding everything, for analysis scripts.
- Per player: score, points from bricks and from rules, bricks broken, paddle hits, own-ball
  hits, steals made, balls stolen, balls lost, lost balls received, possession time, waiting
  time, launch delay, paddle distance, time moving or still, power-ups caught. Per round:
  duration, end reason, team score, the robot's share of the score, bricks broken and left,
  time the paddles overlapped, most balls in play.

## Consequences

- A crash or early quit still leaves a usable partial log. Without the final JSON block, the
  Markdown tables are the record.
- Logs hold participant data, so `logs/` is gitignored.
- New measures go in `stats.py`: count them, then add a row to `ROWS`.
