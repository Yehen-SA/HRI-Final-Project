# Architecture

The layout follows the course's Overcooked template: one file of tuning values, one game
engine, and a separate robot file. The basic game is playable (rules in
[decisions/0005-basic-game-rules.md](decisions/0005-basic-game-rules.md)); study settings,
logging and the web build come next ([plan.md](plan.md)).

## Modules (`src/`)

| File | Job |
|---|---|
| `config.py` | Every game tuning value: window, paddles, balls, bricks, rules, colours. |
| `actions.py` | The actions a paddle can take (`LEFT`, `RIGHT`, `STAY`). Shared by both players. |
| `entities.py` | `Paddle`, `Ball` and `Brick`. Paddles and balls have an `owner`. |
| `human_controls.py` | Keyboard to action for the human, plus the launch (Space) and quit (Esc) keys. Nothing robot-related. |
| `robot_agent.py` | `Robot(strategy)`: the robot, created with a strategy, with `get_action(observation)`. |
| `session.py` | The study session: `Session.flow()` lists the stages in order as a generator of screens; `run_session()` is the window loop with pause and quit. |
| `assignment.py` | Participant ID → conditions (score mode, robot order), with an optional table and `CONDITION_OVERRIDE`. |
| `questions.py` | Question types (`Info`, `Consent`, `MultipleChoice`, `Likert`, `Slider`, `TextAnswer`), with `show_if` for condition-specific questions. |
| `pre_questions.py`, `post_questions.py` | The survey questions: stage 1, after each robot round, and stage 3. |
| `session_text.py` | Instructions and messages between stages. |
| `survey_screen.py` | Shows a list of questions one page at a time (mouse and keyboard). |
| `ui.py` | Fonts, wrapped text, buttons, overlays. |
| `robot_persona/` | The robot as a character: `persona_config.py` (name, look, speech and voice settings), `sprites.py` (expressions; drawn in code or from PNGs), `lines.py` (what it says and when), `speech.py` (bubbles, voice), `persona.py` (`RobotPersona`, a game listener). |
| `paths.py` | Locates `assets/`, including inside packaged builds. |
| `web.py` | Browser-only helpers: downloads the log file. |
| `stats.py` | `RoundStats`: a game listener that measures each round per player (scores, steals, drops, possession time...) and keeps an event timeline. |
| `session_log.py` | `SessionLog`: writes one Markdown log per run to `logs/`, section by section, ending with a JSON block. |
| `rules.py` | Optional rules (penalties, bonuses, power-ups): a `Rule` base class with one hook per game event, and the `RULES` list where each rule is switched on or off. |
| `robot_strategies.py` | The `Strategy` enum (`GOOD`, `BAD`, `SWEEP`) and one class per strategy, tuning values at the top of each. |
| `engine.py` | `Game`: rules, collisions, scoring and the robot's observation, all runnable without a window (`update()`), plus drawing and the async window loop (`run()`). |
| `main.py` | Entry point (`uv run src/main.py`; `--max-frames N` stops early, for tests). |

## Human and robot are kept apart

The two players differ only in where their action comes from (both paddles move at the same
speed; `ROBOT_PADDLE_SPEED` can change that). Once an action exists, the engine moves both paddles with the same
`_apply_action()`.

```
keyboard    → human_controls.read_human_action ─┐
                                                 ├→ Game._apply_action(paddle, action)
observation → Robot(strategy).get_action ────────┘
```

- The robot only sees the observation dict the engine builds. It never reads pygame or the
  keyboard.
- The human side never imports the robot.
- Swapping in a different robot means passing a different `Strategy`, or adding a strategy class
  to `robot_strategies.py`. `Game(robot_strategy=None)` plays with no robot at all.

## Paddle layout

Both paddles share one row (`PADDLE_Y`) and pass through each other: the engine never
checks paddles against each other, only against the ball and the screen edges.
See [decisions/0002-shared-paddle-row.md](decisions/0002-shared-paddle-row.md).

## Balls and ownership

Each player starts with one ball, in their colour: blue for the human, orange for the robot
(`COLOR_HUMAN`, `COLOR_ROBOT`). A ball's colour shows its owner, who scores its next brick.
Hitting a ball in the other player's colour takes it over (a steal). A lost ball counts as a
drop for its owner and goes to a random player (`LOST_BALL_GOES_TO`), waiting on their paddle.
The engine keeps a plain `balls` list, so there can be any number of balls.
See [decisions/0007-colour-follows-scorer.md](decisions/0007-colour-follows-scorer.md).

## Game events

Everything that happens in a round goes through `Game._emit()`: `round_start`, `tick`,
`ball_launched`, `paddle_hit`, `steal`, `brick_broken`, `points`, `ball_lost`, `ball_given`,
`powerup_spawned`, `powerup_caught`, `powerup_missed`, `round_end` (data for each in
`engine.EVENTS`). Enabled rules get `on_<event>(game, ...)`; listeners passed to `Game(...)`
get `listener(event, data)`. Logging and the robot persona hook in as listeners.
See [decisions/0008-rules-framework.md](decisions/0008-rules-framework.md).

## Study session

`main.py` runs the session by default (`--free-play` for plain games):

1. Participant ID → conditions (`assignment.py`): P01 shared/BAD-first, P02 split/BAD-first,
   P03 shared/GOOD-first, P04 split/GOOD-first, then repeating.
2. Stage 1: `PRE_QUESTIONS` (consent first; declining ends the session), then instructions.
3. Stage 2: practice round with no robot (`PRACTICE_SECONDS`), then for each robot in order: an
   intro page, a round (`ROUND_SECONDS`), and `POST_ROUND_QUESTIONS`.
4. Stage 3: `FINAL_QUESTIONS`, then the end screen (shows the log's location).

Every round starts from the same seed. Esc pauses; Esc again quits and the log is marked
aborted (a round in progress is saved with end reason "quit").
See [decisions/0010-in-game-surveys-and-session.md](decisions/0010-in-game-surveys-and-session.md).

## Robot persona

The window is 720 px tall: the play area ends at `PLAY_BOTTOM` (600), and the strip below is
the robot's. `RobotPersona` draws the robot under its paddle with arms holding it up, so the
paddle looks controlled by it. It listens to game events: each reaction shows an expression
for a moment, and sometimes a line in a speech bubble beside the robot (never over the play
area), with a voice file if one exists. It behaves the same for both strategies and score
modes. Lines it says go into the log's timeline as `robot_said`.
See [decisions/0011-robot-persona.md](decisions/0011-robot-persona.md).

## Logging

Each run writes a new file `logs/<date>_<time>_<participant>.md` (next to the exe when
packaged); an existing file is never overwritten. Each section is flushed as soon as it's
written, so a crash keeps everything so far. The log holds the conditions, settings (config,
rules, robot tuning), survey answers, a stats table per round (`Measure | Human | Robot`), an
event timeline, and a final JSON block with the same data.
See [decisions/0009-markdown-session-log.md](decisions/0009-markdown-session-log.md).

## Packaging

`python_build/` is the only source. `../build_html.py` stages `src/` and `assets/` into the
layout pygbag wants and builds `../html_build/`; `../build_exe.ps1` (run on Windows) builds
`../exe_build/HRI_Breakout.exe` with PyInstaller. Browser rules the code follows: `main.py`
imports pygame itself and ends in a plain `asyncio.run()`; the `statistics` module isn't used
(it's missing in the browser); logs are downloaded at the end (`web.py`).
See [decisions/0012-packaging.md](decisions/0012-packaging.md).

## Where to tune what

- **Game feel and rules** (ball speed, paddle sizes and speeds, bricks and their points,
  round length, score mode, seed, whether paddles can hit each other's ball): `config.py`.
- **What's logged:** measures in `stats.py` (`ROWS` lists the table rows); `LOG_TIMELINE` in
  `config.py` switches the event timeline.
- **Optional rules:** switch them on and off in the `RULES` list at the bottom of `rules.py`.
- **Robot behaviour:** the strategy classes in `robot_strategies.py`; the free-play strategy is
  `ROBOT_STRATEGY` in `config.py`. Compare strategies with `uv run tools/simulate_robot.py`.

## Still to build

See [plan.md](plan.md): study settings and robot skill presets, the session (practice plus
three rounds), event logging, and the web build. Rule ideas left out of the basic game are in
[deferred.md](deferred.md).
