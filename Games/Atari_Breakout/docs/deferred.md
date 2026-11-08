# Deferred game rules

These rules are left out of the code on purpose until the study design settles what they
should be. The engine has no lives, no scoring and no rule for a lost ball yet.

## What happens when a ball is lost

Idea so far:

- A countdown appears on that player's side of the screen, in their colour (human on the
  left, robot on the right): "New ball from paddle in 5", 4, 3...
- The delay is somewhere around 5 to 10 seconds.
- While it counts down, that player's paddle is frozen, so they can't help with the other
  ball. The engine would apply the freeze, so the robot is held to it too.
- At zero, a new ball launches from that player's paddle.

## Lives

Not decided. Options: shared team lives, lives per player, or no lives and a fixed-length
round instead.

## Scoring

Not decided. Options: one team score, a score per player (by whose ball broke the brick),
or both.

## End of a round

Not decided: when all bricks are gone, after a fixed time, or when lives run out.
