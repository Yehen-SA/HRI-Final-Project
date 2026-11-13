"""Optional game rules. Switch a rule on or off with `enabled` in the RULES list at the bottom.

The core rules (brick points, ball colour = owner, lost balls go to a random player) live in
the engine and config.py. This file is for extra rules to experiment with, such as penalties,
bonuses and power-ups.

Writing a rule
--------------
Subclass `Rule` and fill in only the hooks you need. Each hook gets the `game` first, then the
event's data. For example, a bonus for every steal:

    class StealBonus(Rule):
        def on_steal(self, game, paddle, ball, from_player):
            game.add_points(paddle.owner, 2, "steal bonus")

Then add `StealBonus(enabled=True)` to RULES.

What a rule can use
-------------------
- `game.add_points(player, points, reason)`: give or (negative) take points. The reason shows
  up in the log, separate from brick points.
- `game.spawn_ball(owner, x, y)`: add an extra ball, launched upwards from (x, y). Extra balls
  vanish when lost instead of coming back.
- `game.spawn_powerup(kind, x, y)`: drop a power-up; `on_powerup_caught` fires if a paddle
  catches it. The rule decides what it does.
- `game.rules_rng`: random numbers for rules (seeded, so runs repeat).
- Read-only state: `game.scores`, `game.balls`, `game.paddles`, `game.bricks`, `game.tick`,
  `game.drops`, `game.steals`.
- Players are the strings "human" and "robot". `paddle.owner` and `ball.owner` are one of them.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Rule:
    """Base class: every hook does nothing until a rule overrides it."""

    enabled: bool = True

    @property
    def name(self) -> str:
        return type(self).__name__

    def settings(self) -> dict[str, Any]:
        """The rule's settings, for the log."""
        return {k: v for k, v in vars(self).items() if k != "enabled"}

    # --- Hooks ---

    def on_round_start(self, game) -> None:
        """A round has been set up."""

    def on_tick(self, game) -> None:
        """Called once per frame (60 times a second), after everything has moved."""

    def on_ball_launched(self, game, ball) -> None:
        """A ball has left a paddle (launched or spawned)."""

    def on_paddle_hit(self, game, paddle, ball) -> None:
        """A paddle bounced a ball. `ball.owner` is already the paddle's owner."""

    def on_steal(self, game, paddle, ball, from_player) -> None:
        """A paddle hit a ball in the other player's colour and took it over."""

    def on_brick_broken(self, game, ball, brick) -> None:
        """A ball broke a brick; its points have already gone to `ball.owner`."""

    def on_points(self, game, player, points, reason) -> None:
        """Points were added (bricks or a rule). Careful: adding points here loops."""

    def on_ball_lost(self, game, ball) -> None:
        """A ball fell off the bottom. `ball.owner` is who lost it (before it's given away)."""

    def on_ball_given(self, game, ball, player) -> None:
        """A lost ball was given to `player` and is waiting on their paddle."""

    def on_powerup_spawned(self, game, powerup) -> None:
        """A power-up started falling."""

    def on_powerup_caught(self, game, paddle, powerup) -> None:
        """A paddle caught a power-up."""

    def on_powerup_missed(self, game, powerup) -> None:
        """A power-up fell off the bottom."""

    def on_round_end(self, game, reason) -> None:
        """The round ended: "timer", "bricks_cleared" or "quit"."""


# --- Example rules (all off by default) ---


@dataclass
class LostBallPenalty(Rule):
    """Losing a ball costs points. The score never goes below zero."""

    points: int = 3

    def on_ball_lost(self, game, ball) -> None:
        penalty = min(self.points, game.scores[ball.owner])
        if penalty:
            game.add_points(ball.owner, -penalty, "lost ball penalty")


@dataclass
class StealBonus(Rule):
    """Taking over the other player's ball earns points."""

    points: int = 2

    def on_steal(self, game, paddle, ball, from_player) -> None:
        game.add_points(paddle.owner, self.points, "steal bonus")


@dataclass
class MultiBallPowerUp(Rule):
    """A broken brick sometimes drops a power-up. Catching it adds a ball in your colour."""

    drop_chance: float = 0.15

    def on_brick_broken(self, game, ball, brick) -> None:
        if game.rules_rng.random() < self.drop_chance:
            game.spawn_powerup("multiball", brick.rect.centerx, brick.rect.bottom)

    def on_powerup_caught(self, game, paddle, powerup) -> None:
        if powerup.kind == "multiball":
            game.spawn_ball(paddle.owner, paddle.centre_x, paddle.y - 10)


# --- Rules in use: flip `enabled` to switch one on ---

RULES: list[Rule] = [
    LostBallPenalty(enabled=False, points=3),
    StealBonus(enabled=False, points=2),
    MultiBallPowerUp(enabled=False, drop_chance=0.15),
]


def enabled_rules() -> list[Rule]:
    return [rule for rule in RULES if rule.enabled]
