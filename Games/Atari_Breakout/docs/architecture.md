# Architecture

The layout follows the course's Overcooked template: one file of tuning values, one game
engine, and a separate robot file. Gameplay is not implemented yet; the files hold the
structure, tuning values and function signatures.

## Modules (`src/`)

| File | Job |
|---|---|
| `config.py` | Every game tuning value: window, paddles, balls, bricks, rules, colours. |
| `actions.py` | The actions a paddle can take (`LEFT`, `RIGHT`, `STAY`). Shared by both players. |
| `entities.py` | `Paddle`, `Ball` and `Brick`. Paddles and balls have an `owner`. |
| `human_controls.py` | Keyboard to action for the human. Nothing robot-related. |
| `robot_agent.py` | The robot: its tuning values at the top, then `get_robot_action(observation)`. |
| `engine.py` | `Game`: the loop, collisions, scoring, drawing, and building the robot's observation. |
| `main.py` | Entry point (`uv run src/main.py`). |

## Human and robot are kept apart

The two players differ only in where their action comes from. Once an action exists, the
engine moves both paddles with the same `_apply_action()`, so neither gets different rules.

```
keyboard    → human_controls.read_human_action ─┐
                                                 ├→ Game._apply_action(paddle, action)
observation → robot_agent.get_robot_action ─────┘
```

- The robot only sees the observation dict the engine builds. It never reads pygame or the
  keyboard.
- The human side never imports the robot.
- Swapping in a different robot means replacing `get_robot_action()` and nothing else.

## Paddle layout

Both paddles share one row (`PADDLE_Y`) and pass through each other: the engine never
checks paddles against each other, only against the ball and the screen edges.
See [decisions/0002-shared-paddle-row.md](decisions/0002-shared-paddle-row.md).

## Two balls

Each player has their own ball in their own colour: blue for the human, orange for the
robot (`COLOR_HUMAN`, `COLOR_ROBOT`). By default a paddle only bounces its own ball and the
other ball passes through it. Set `PADDLES_HIT_ANY_BALL = True` in `config.py` to let either
paddle bounce either ball.
See [decisions/0004-two-colour-coded-balls.md](decisions/0004-two-colour-coded-balls.md).

## Where to tune what

- **Game feel and difficulty** (ball speed, paddle size, bricks, whether paddles can
  hit each other's ball): `config.py`.
- **Robot skill** (reaction delay, speed, aim error, miss chance, prediction): the top of
  `robot_agent.py`.

## Still to design

- Game rules: lives, scoring, and what happens when a ball is lost. Deferred on purpose;
  see [deferred.md](deferred.md).
- Study conditions (how a condition changes the robot or the HUD).
- Logging per round for analysis.
