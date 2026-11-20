# 0014: Steals, rescues and scripted help requests

Status: accepted (changes the double-touch rule in 0007)

## Context

The report measures in-game behaviour as two rates: **steals** (taking the robot's ball when
the robot could have returned it) and **rescues** (saving a robot ball it couldn't return),
with rescues split into prompted and unprompted, and each robot prompting the same number of
times. The robot's speech about steals must also be capped so both robots talk equally.

## Decision

- When a ball reaches the paddles: only its owner's paddle touches it, the owner keeps it;
  both paddles touch it (they overlap), the other player **steals** it; only the other
  player's paddle touches it, that's a **rescue**. Either way the ball takes the new owner's
  colour. Counted for both the human and the robot. (0007 gave a double touch to the owner;
  it now goes to the other player as a steal.)
- Rates divide by chances: steal rate = steals / the other's balls that reached the other's
  paddle; rescue rate = rescues / the other's balls the other couldn't reach.
- **Scripted misses:** in each robot round the robot lets `HELP_REQUESTS_PER_ROUND` (2) of its
  own balls go on purpose, spread evenly over the round, and asks for help. Its paddle can't
  bounce that ball and moves out of its way, whatever the strategy, so both robots prompt
  equally. Saving it is a prompted rescue; other rescues are unprompted.
- GOOD leaves the human's balls alone when the human could still reach them (so it doesn't
  steal on purpose), and goes for them only when the human can't (a rescue).
- Voice lines are configured through one `VoiceTrigger` per situation (`lines.py`): chance,
  priority, `max_per_round` and `cooldown_s`. Steal and rescue reactions are capped (3 per
  round each), and the counts per trigger are logged.

## Consequences

- Robot steals still happen when both paddles happen to be under one of the human's balls
  (GOOD about 6 per round against a player who chases every ball, in simulation).
- A help request waits for a robot ball falling high enough for the human to react, so a round
  can end with fewer than 2 if the robot has no ball at the right time. The log records how
  many were made.
- Simulations (`tools/simulate_robot.py`) turn help requests off, to measure skill alone.

## Later change: start screen

Each round (and free-play game) now opens on a start screen (`Game(wait_for_launch=True)`):
nothing moves, the robot introduces itself (its bubble stays up), and play and the timer start
when the human launches their first ball with Space (event `play_started`). Help requests are
timed from then.
