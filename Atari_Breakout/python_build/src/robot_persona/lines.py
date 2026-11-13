"""What the robot says, and when.

Each trigger has a list of lines; one is picked at random when the trigger fires. Edit the
text freely; after changing it, regenerate the voice files:

    uv run tools/generate_voice.py

Triggers (fired by persona.py from game events):
  round_start    a round begins
  robot_brick    the robot's ball broke a brick
  human_brick    the human's ball broke a brick
  robot_steal    the robot hit a ball in the human's colour
  human_steal    the human hit a ball in the robot's colour
  robot_lost     the robot lost a ball
  human_lost     the human lost a ball
  powerup        someone caught a power-up (only with power-up rules on)
  idle           nothing said for a while
  round_end      the round is over

`chance` is how likely the robot is to speak when the trigger fires (it always reacts with
its face). `priority` lets an important line interrupt a less important one.
"""

from dataclasses import dataclass, field

from robot_persona.sprites import Expression


@dataclass
class Trigger:
    expression: Expression
    chance: float
    priority: int
    lines: list[str] = field(default_factory=list)


TRIGGERS: dict[str, Trigger] = {
    "round_start": Trigger(
        Expression.EXCITED,
        chance=1.0,
        priority=3,
        lines=["Hi! Let's do this.", "Ready when you are!", "Okay, let's play!"],
    ),
    "robot_brick": Trigger(
        Expression.HAPPY,
        chance=0.2,
        priority=1,
        lines=["Got one!", "Nice!", "Another brick down."],
    ),
    "human_brick": Trigger(
        Expression.HAPPY,
        chance=0.15,
        priority=1,
        lines=["Good shot!", "Nice one!", "Great hit!"],
    ),
    "robot_steal": Trigger(
        Expression.EXCITED,
        chance=0.7,
        priority=2,
        lines=["I've got this one!", "Mine!", "Caught it!"],
    ),
    "human_steal": Trigger(
        Expression.SURPRISED,
        chance=0.7,
        priority=2,
        lines=["Oh, you got that one!", "Whoa, nice catch!", "You took that one!"],
    ),
    "robot_lost": Trigger(
        Expression.SAD,
        chance=0.6,
        priority=2,
        lines=["Oops, missed it.", "Oh no!", "Sorry, that one got away."],
    ),
    "human_lost": Trigger(
        Expression.SAD,
        chance=0.4,
        priority=2,
        lines=["So close!", "Unlucky!", "Almost had it."],
    ),
    "powerup": Trigger(
        Expression.EXCITED,
        chance=0.8,
        priority=2,
        lines=["Extra ball!", "Ooh, a power-up!"],
    ),
    "idle": Trigger(
        Expression.NEUTRAL,
        chance=1.0,
        priority=0,
        lines=["Keep going!", "We're doing well.", "Watch the balls!"],
    ),
    "round_end": Trigger(
        Expression.HAPPY,
        chance=1.0,
        priority=3,
        lines=["That was fun!", "Good game!", "Well played!"],
    ),
}


def all_lines() -> list[tuple[str, str]]:
    """Every (trigger, text) pair, for the voice generator."""
    return [(name, text) for name, t in TRIGGERS.items() for text in t.lines]
