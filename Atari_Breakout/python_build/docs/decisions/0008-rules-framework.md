# 0008: Optional rules live in rules.py, driven by game events

Status: accepted

## Context

We want to try rules that make the game more competitive (penalties for lost balls, rewards for
steals, Atari-style power-ups) and switch them on and off easily, without editing the engine
each time.

## Decision

- The engine announces every game event through one method, `Game._emit()`. The events and
  their data are listed in `engine.EVENTS`.
- `rules.py` has a `Rule` base class with a no-op hook per event (`on_steal`, `on_ball_lost`,
  ...). A rule overrides only the hooks it needs, and acts through a small API:
  `game.add_points(player, points, reason)`, `game.spawn_ball(...)`, `game.spawn_powerup(...)`.
- `RULES` at the bottom of `rules.py` lists the rules, each with `enabled=True/False`. The three
  ideas (`LostBallPenalty`, `StealBonus`, `MultiBallPowerUp`) are written as examples, all off.
- Core rules (brick points, ball ownership, lost-ball respawn) stay in the engine and config.
- Points are recorded by reason (`bricks`, `steal bonus`, ...), so bonuses and penalties are
  separate from brick points in the log.
- Rules get their own seeded RNG, so switching a rule on doesn't change launch angles or
  respawns.
- Extra balls from rules vanish when lost; the starting balls always come back.

## Consequences

- A new rule is a small class plus one line in `RULES`.
- The same events feed logging (step 4) and the robot persona (step 6) as listeners.
- A rule can break the game's balance or loop (adding points in `on_points`); the hooks'
  docstrings warn about this.
