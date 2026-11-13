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

This folder is the source for all three versions (Python, browser, Windows .exe); see
[../README.md](../README.md).

## Setup

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```sh
uv sync
```

## Run

```sh
uv run src/main.py             # the study session: ID, surveys, practice, two robot rounds
uv run src/main.py --free-play # just play (each game is still logged)
```

The session asks for a participant ID, which decides the conditions (score mode and robot
order, see [src/assignment.py](src/assignment.py)). Then: stage 1 questions, a practice round
without the robot, a round with each robot followed by questions, stage 3 questions.

Controls: A/D or the arrow keys move, Space launches a waiting ball. Esc pauses; Esc again
quits (the log is kept, marked aborted).

Testing options: `--pid P07` skips the ID screen, `--autoplay` answers and plays by itself,
`--round-seconds 5` shortens every round.

## Editing the surveys

- Stage 1 questions: [src/pre_questions.py](src/pre_questions.py)
- After each robot round, and stage 3: [src/post_questions.py](src/post_questions.py)
- Question types (multiple choice, Likert, slider, text, info, consent):
  [src/questions.py](src/questions.py)
- Instructions and messages between stages: [src/session_text.py](src/session_text.py)
- The order of the stages: `Session.flow()` in [src/session.py](src/session.py)

## The robot's persona

The robot sits under its paddle, holding it up, and reacts to the game with its face and
speech bubbles (with voice). Everything about it is in
[src/robot_persona/](src/robot_persona/):

- The two robots' names and colours (Nova, orange, in round 1; Pip, pink, in round 2), plus
  size, speech and voice settings: `persona_config.py`
- What it says and when: `lines.py`. After editing lines, regenerate the voice files with
  `uv run tools/generate_voice.py` (Piper, offline).
- Its look: drawn in code (`sprites.py`). To use your own art, add one PNG per expression to
  `assets/robot/` (`neutral.png`, `happy.png`, `sad.png`, `surprised.png`, `focused.png`,
  `excited.png`); they're used automatically once all six exist. Put them in
  `assets/robot/nova/` or `assets/robot/pip/` to give each robot its own art.

## Logs

Every run writes a Markdown log to `logs/` (a new file each time, never overwritten): the
settings, the scores and behaviour stats per round, an event timeline, and a JSON block for
analysis.

## Packaging for subjects

- Browser: `uv run ../build_html.py` builds `../html_build/` (then host it; see its README).
- Windows: run `../build_exe.ps1` on Windows to build `../exe_build/HRI_Breakout.exe`.

Code that must behave differently when packaged: `paths.py` (where `assets/` is),
`session_log.default_log_dir()` (where logs go), and `web.py` (the browser downloads the log).

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
- Optional rules (penalties, bonuses, power-ups): the `RULES` list in
  [src/rules.py](src/rules.py)
- Robot behaviour: [src/robot_strategies.py](src/robot_strategies.py); compare strategies with
  `uv run tools/simulate_robot.py`

## Layout

| Path | What's in it |
|---|---|
| `src/config.py` | All game tuning values |
| `src/actions.py` | Paddle actions shared by human and robot |
| `src/entities.py` | Paddle, ball and brick |
| `src/human_controls.py` | Keyboard input for the human |
| `src/session.py` | The study session: stages, rounds, pause/quit |
| `src/assignment.py` | Participant ID → conditions |
| `src/questions.py` | Question types for surveys |
| `src/pre_questions.py`, `src/post_questions.py` | Survey questions |
| `src/session_text.py` | Instructions and messages |
| `src/survey_screen.py`, `src/ui.py` | Survey pages and drawing helpers |
| `src/stats.py` | Per-round measures for the log |
| `src/session_log.py` | Writes the Markdown log |
| `src/robot_persona/` | The robot as a character: look, expressions, speech, voice |
| `src/paths.py` | Finds the assets folder (also when packaged) |
| `src/rules.py` | Optional rules, switched on or off |
| `src/robot_agent.py` | `Robot(strategy)` |
| `src/robot_strategies.py` | Robot strategies (`GOOD`, `BAD`, `SWEEP`) |
| `src/engine.py` | Game loop |
| `tools/` | Helper scripts (robot simulation, voice generation) |
| `tests/unit/` | Unit tests for single modules |
| `tests/e2e/` | End-to-end tests that run the whole game |
| `assets/` | Images and sounds |
| `docs/` | Build plan, architecture notes and decision records |
