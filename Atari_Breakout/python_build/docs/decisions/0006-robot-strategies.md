# 0006: Two robot strategies, chosen by enum

Status: accepted

## Context

The study compares a robot that plays badly with one that plays well. Both must look like the
same robot apart from how well it plays, and it must be easy to swap between them.

## Decision

- `robot_strategies.py` holds a `Strategy` enum and one class per strategy. `Robot(Strategy.X)`
  in `robot_agent.py` wraps the chosen one.
- `BAD`: random movement. It picks left, right or stay and holds it for 10–40 frames, ignoring
  the balls.
- `GOOD`: goes for the falling ball that will land soonest (any colour) and aims at its
  predicted landing point. A reaction delay (8 frames), aim error (±30 px) and an occasional
  misjudged ball (8%) keep it from looking perfect.
- `SWEEP`: the old sweeping robot, kept for testing.
- Both robots move at the human's paddle speed. Each robot has its own seeded RNG.

## Consequences

- With the 10-row wall and 2-minute rounds: GOOD about 95%, BAD about 44%.
- In robot-only simulation (`tools/simulate_robot.py`), GOOD catches about 96% of its balls and
  BAD about 31%.
- Points per minute differ less (about 67 vs 54), because a ball breaks bricks while it's in the
  air whoever catches it. The score gap between conditions is smaller than the catch gap.
- `Game(robot_strategy=None)` plays without a robot (for the practice round).
