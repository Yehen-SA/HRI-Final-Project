# 0013: Each round's robot has its own name and colour

Status: accepted

## Context

With one name ("Robo") for both robots, subjects might see one robot that played differently
in each round, rather than two robots. Distinct identities make each robot easier to judge on
its own, and let questions compare them by name.

## Decision

- Two identities in `persona_config.IDENTITIES`: **Nova** (orange) and **Pip** (pink). The
  colour is used for that robot's paddle, balls, body and HUD label. Pink was chosen over
  purple, which looks too close to the human's blue.
- Identities go by round, not strategy: round 1 is always Nova, round 2 always Pip. Robot order
  is counterbalanced, so each name is the BAD robot for half the participants and the GOOD
  robot for the other half. That keeps name and colour separate from skill (the confound the
  report flags).
- Only name and colour differ. Voice, expressions and lines are the same for both robots.
- Questions use `{robot_name}` (the current robot), and `{robot_1_name}` / `{robot_2_name}` to
  compare them. Multiple-choice options can use these placeholders too. The final question asks
  which robot felt more like a teammate, by name.
- The log records the names per round, and the robot names in the participant's conditions.

## Consequences

- Name and colour are always confounded with round position (Nova is always first). Round
  position is already a factor in the counterbalanced design, so the analysis can account for
  it.
- Free play uses Nova.
