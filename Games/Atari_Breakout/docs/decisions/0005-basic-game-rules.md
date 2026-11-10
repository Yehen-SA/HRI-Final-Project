# 0005: Rules for the basic game

Status: accepted

## Context

Before adding study settings, logging and a web build, we want the simplest version of the
game that plays well, with no extra rules. The rules below were agreed one by one.

## Decision

- **Robot:** no AI yet. Its paddle sweeps the full screen width, turning at each edge, at its
  own speed (`ROBOT_PADDLE_SPEED`, slower than the human's).
- **Balls:** two balls, colour coded by owner. Either paddle can bounce either ball
  (`PADDLES_HIT_ANY_BALL = True`). Balls pass through each other. Constant speed.
- **Paddle bounce:** the angle depends on where the ball hits the paddle (up to
  `MAX_BOUNCE_ANGLE_DEG` at the edges).
- **Launching:** a ball waits on its owner's paddle at the start and after it's lost. The human
  presses Space; the robot's ball launches after `ROBOT_RELAUNCH_DELAY_S`. Launch angle is
  random in a range, from a seeded RNG (`SEED`).
- **No lives:** a dropped ball only costs time. Drops are counted.
- **Scoring:** rows are worth 7, 7, 4, 4, 1, 1 from the top. Points go to the paddle that last
  hit the ball (the owner if no paddle has hit it since launch). If both paddles touch a ball
  in the same frame, the owner's paddle counts.
- **HUD:** `SCORE_MODE` shows a team score (`shared`) or both scores plus the total (`split`),
  and the time left.
- **End:** the timer (`ROUND_SECONDS`) runs out or every brick is gone, whichever is first.

## Consequences

- The robot paddle moves at a different speed from the human's, so the two paddles no longer
  follow identical movement rules (they still share the same movement code).
- With either paddle able to hit either ball, players can rescue each other's ball and take the
  credit for the bricks it breaks next, which the logs will need to capture.
- A ball breaks bricks while in flight whoever is catching it, so even the sweeping robot
  scores. Score share reflects both catching and luck of the ball's path.
- Each rule is a config value, so the study phase can change them without code changes.
