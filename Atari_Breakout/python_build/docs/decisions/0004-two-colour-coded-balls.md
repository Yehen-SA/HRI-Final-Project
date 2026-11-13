# 0004: Two balls, colour coded by player

Status: accepted; colours now follow ownership, see
[0007](0007-colour-follows-scorer.md)

## Context

With both paddles on one row and able to pass through each other, a single ball makes it
unclear whose job it is to catch it, and who to credit or blame for a save or a miss.

## Decision

Each player has their own ball in their own colour: blue for the human, orange for the robot
(the same colours as their paddles). By default a paddle only bounces its own ball. Whether
a paddle can also bounce the other player's ball is a setting (`PADDLES_HIT_ANY_BALL` in
`config.py`).

## Consequences

- Each player's responsibility is visible at a glance, and every catch or drop can be logged
  against one player.
- Turning `PADDLES_HIT_ANY_BALL` on lets players rescue each other's ball, which could be a
  study condition (for example, a robot that helps versus one that doesn't).
- The robot's observation includes both balls, so a helping robot is possible without
  changing the engine.
