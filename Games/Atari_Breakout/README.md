# Atari Breakout

A Breakout game for the HRI final project user study. Written in Python with
[pygame-ce](https://pyga.me/).

Status: project structure only, no gameplay yet.

## Setup

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```sh
uv sync
```

## Run

```sh
uv run breakout
```

## Test

```sh
uv run pytest          # all tests
uv run pytest -m unit  # unit tests only (tests/unit/)
uv run pytest -m e2e   # end-to-end tests only (tests/e2e/)
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Layout

| Path | What's in it |
|---|---|
| `src/breakout/` | Game source code |
| `tests/unit/` | Unit tests for single modules |
| `tests/e2e/` | End-to-end tests that run the whole game |
| `assets/` | Images and sounds |
| `docs/` | Design notes and decision records |
