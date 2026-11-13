# Deferred game rules

The basic game's rules are now decided: see
[decisions/0005-basic-game-rules.md](decisions/0005-basic-game-rules.md). This file keeps the
ideas that were left out of the basic version, for the study phase
(see [plan.md](plan.md)).

## Countdown after a lost ball

Instead of waiting on the paddle for a launch:

- A countdown appears on that player's side of the screen, in their colour (human on the
  left, robot on the right): "New ball from paddle in 5", 4, 3...
- The delay is somewhere around 5 to 10 seconds.
- While it counts down, that player's paddle is frozen, so they can't help with the other
  ball. The engine would apply the freeze, so the robot is held to it too.
- At zero, a new ball launches from that player's paddle.

## Lives

The basic game has none (fixed-length rounds). Options if needed: shared team lives or lives
per player.

## Ball speed-up

The basic game keeps ball speed constant. The original idea was +0.1 per paddle hit, capped.

## When all bricks are gone

The basic game ends early. For fixed-length study rounds, the grid could refill instead.
