# 0007: Ball colour follows who scores; lost balls go to a random player

Status: accepted; the double-touch rule is changed by
[0014](0014-steals-rescues-and-help-requests.md)

## Context

With fixed ball colours (0004) and points going to the last hitter (0005), a blue ball could
score for the robot. The colour no longer told the player who would score, which made the
scoring hard to follow.

## Decision

- A ball's colour is its owner: whoever last hit it, and who scores its next brick. Each player
  starts with one ball in their colour.
- Hitting a ball in the other player's colour takes it over. This is counted as a steal.
- If both paddles touch a ball in the same frame, its current owner keeps it.
- A lost ball counts as a drop for its owner, then goes to a random player (seeded 50/50,
  `LOST_BALL_GOES_TO = "random"`; `"human"` or `"robot"` for testing). It waits on their paddle.
  With no robot it always goes to the human.
- Space launches one of the human's waiting balls per press. The robot's launch after
  `ROBOT_RELAUNCH_DELAY_S`. Several waiting balls sit side by side.

## Consequences

- The screen always shows who would score each ball.
- One player can hold both balls while the other has none. Random respawn balances this out on
  average.
- Steals and drops per player are counted, ready for logging.
