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

## Two balls

Each player has their own ball in their own colour: blue for the human, orange for the
robot (`COLOR_HUMAN`, `COLOR_ROBOT`). With `PADDLES_HIT_ANY_BALL = True` (the current
setting) either paddle bounces either ball; set it to `False` so a paddle only bounces its own.
Points for a brick go to whoever last hit the ball.
See [decisions/0004-two-colour-coded-balls.md](decisions/0004-two-colour-coded-balls.md).

## Where to tune what

- **Game feel and rules** (ball speed, paddle sizes and speeds, bricks and their points,
  round length, score mode, seed, whether paddles can hit each other's ball): `config.py`.
- **Robot behaviour:** the strategy classes in `robot_strategies.py`; the free-play strategy is
  `ROBOT_STRATEGY` in `config.py`. Compare strategies with `uv run tools/simulate_robot.py`.

## Still to build

See [plan.md](plan.md): study settings and robot skill presets, the session (practice plus
three rounds), event logging, and the web build. Rule ideas left out of the basic game are in
[deferred.md](deferred.md).
