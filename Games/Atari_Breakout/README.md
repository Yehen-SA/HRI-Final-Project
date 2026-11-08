# Atari Breakout

A Breakout game for the HRI final project user study. Written in Python with
[pygame-ce](https://pyga.me/).

Status: structure, tuning values and function signatures only. No gameplay yet.

A human and a robot each control a paddle on the same row (they can pass through each other)
and each has their own ball, colour coded to match: blue for the human, orange for the robot.
They play as a team.
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

## Test

```sh
uv run pytest          # all tests
uv run pytest -m unit  # unit tests only (tests/unit/)
uv run pytest -m e2e   # end-to-end tests only (tests/e2e/)
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Tuning

- Game values (ball speed, paddle size, bricks, lives, colours): [src/config.py](src/config.py)
- Robot skill (reaction delay, speed, aim error, miss chance): top of [src/robot_agent.py](src/robot_agent.py)

## Layout

| Path | What's in it |
|---|---|
| `src/config.py` | All game tuning values |
| `src/actions.py` | Paddle actions shared by human and robot |
| `src/entities.py` | Paddle, ball and brick |
| `src/human_controls.py` | Keyboard input for the human |
| `src/robot_agent.py` | Robot tuning and behaviour |
| `src/engine.py` | Game loop |
| `tests/unit/` | Unit tests for single modules |
| `tests/e2e/` | End-to-end tests that run the whole game |
| `assets/` | Images and sounds |
| `docs/` | Architecture notes and decision records |
