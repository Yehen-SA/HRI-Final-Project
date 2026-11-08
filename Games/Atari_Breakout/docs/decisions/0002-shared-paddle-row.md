# 0002: Paddles share one row and pass through each other

Status: accepted

## Context

Breakout normally has one paddle. The study needs a human and a robot to play as a team.
We first tried a robot row above the human's, but then the robot always meets the ball
first, which makes the human's role depend too much on the robot.

## Decision

Both paddles sit on the same row (`PADDLE_Y` in `config.py`) and can pass through each
other. The human starts on the left, the robot on the right.

## Consequences

- Neither player gets to the ball first by position alone, so both have an equal role.
- No blocking means neither player can get in the other's way, so the robot can't win a
  collision and the human can't be trapped.
- Overlapping paddles don't make it unclear who hit a ball, because each player has their
  own ball (see 0004).
