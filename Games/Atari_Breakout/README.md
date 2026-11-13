# Atari Breakout

A Breakout game for the HRI final project user study. Written in Python with
[pygame-ce](https://pyga.me/).

Status: basic game playable. Study settings, logging and the web version are next; see
[docs/plan.md](docs/plan.md).

A human and a robot each control a paddle on the same row (they can pass through each other)
and each starts with a ball in their colour: blue for the human, orange for the robot. A ball
takes the colour of whoever last hit it, and that player scores its next brick. A lost ball
goes to a random player. They play as a team. The robot has two strategies: `GOOD` (tries to play properly) and `BAD`
(random movement).
See [docs/architecture.md](docs/architecture.md).

## Setup

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```sh
uv sync
```

## Run

```sh
uv run src/main.py
```

Controls: A/D or the arrow keys move, Space launches a waiting ball (and plays again after game
over), Esc quits. Rules: [docs/decisions/0005-basic-game-rules.md](docs/decisions/0005-basic-game-rules.md).

## Test

```sh
uv run pytest          # all tests
uv run pytest -m unit  # unit tests only (tests/unit/)
uv run pytest -m e2e   # end-to-end tests only (tests/e2e/)
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Tuning

- Game values and rules (ball speed, paddles, bricks and points, round length, score mode,
  colours): [src/config.py](src/config.py)
- Robot behaviour: [src/robot_strategies.py](src/robot_strategies.py); compare strategies with
  `uv run tools/simulate_robot.py`

## Layout

| Path | What's in it |
|---|---|
| `src/config.py` | All game tuning values |
| `src/actions.py` | Paddle actions shared by human and robot |
| `src/entities.py` | Paddle, ball and brick |
| `src/human_controls.py` | Keyboard input for the human |
| `src/robot_agent.py` | `Robot(strategy)` |
| `src/robot_strategies.py` | Robot strategies (`GOOD`, `BAD`, `SWEEP`) |
| `src/engine.py` | Game loop |
| `tools/` | Helper scripts (robot simulation) |
| `tests/unit/` | Unit tests for single modules |
| `tests/e2e/` | End-to-end tests that run the whole game |
| `assets/` | Images and sounds |
| `docs/` | Build plan, architecture notes and decision records |
