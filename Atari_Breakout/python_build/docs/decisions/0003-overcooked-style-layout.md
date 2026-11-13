# 0003: Follow the Overcooked template layout

Status: accepted

## Context

The course provides an Overcooked-style game with a simple layout: a constants file, an
engine, and a separate `robot_agent.py` with `get_robot_action(observation) -> action`.
We want the Breakout game just as easy to change, and the robot easy to tune for study
conditions.

## Decision

- All game tuning values live in `config.py`.
- Human input lives only in `human_controls.py`; robot behaviour and its tuning live only in
  `robot_agent.py`.
- Both players produce actions from `actions.py`, and the engine applies them with the same
  code.

## Consequences

- Changing the robot for a condition means editing one file.
- The robot can't cheat by reading game internals: it only gets the observation dict.
