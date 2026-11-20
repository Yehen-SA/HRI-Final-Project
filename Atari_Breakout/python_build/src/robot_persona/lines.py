"""What the robot says, and when: one VoiceTrigger per game situation.

Every trigger has the same settings, so all voice lines are configured the same way:

    expression     the face it pulls (always, even when it doesn't speak)
    lines          what it can say; one is picked at random, not the same as last time
    chance         how likely it is to speak when the trigger fires (0 to 1)
    priority       0-3; a higher-priority line can interrupt a lower one. 3 also skips the
                   global cooldown (persona_config.SPEECH_COOLDOWN_S)
    max_per_round  most times it speaks this trigger in one round (None: no limit)
    cooldown_s     least time between two lines from this trigger (on top of the global one)

`max_per_round` keeps speech balanced between the two robots: e.g. the robot reacts to the
player stealing its ball at most STEAL_LINES_MAX times, however often the player steals.

After editing any line's text, regenerate the voice files:

    uv run tools/generate_voice.py

Lines can use {name} and {colour} (the robot's name and colour); a voice file is made for each
robot.

Triggers (persona.py fires them from game events):
  introduction                 the round's start screen; the bubble stays until play starts
  round_start, round_end       play begins (the player launches the first ball) / ends
  robot_brick, human_brick     a ball in the robot's / player's colour broke a brick
  human_steal                  the player took the robot's ball while the robot was under it
  human_rescue                 the player saved a robot ball the robot couldn't reach
  human_prompted_rescue        the player saved a ball the robot asked for help with
  robot_steal, robot_rescue    the same, the other way round
  help_request                 the robot lets one of its balls go and asks for help
                               (scripted; how many: config.HELP_REQUESTS_PER_ROUND)
  help_missed                  nobody saved the ball the robot asked for help with
  robot_lost, human_lost       a ball fell off the bottom (other cases)
  powerup                      someone caught a power-up (only with power-up rules on)
  idle                         nothing said for a while (persona_config.IDLE_LINE_AFTER_S)
"""

from dataclasses import dataclass, field

import config
from robot_persona.persona_config import IDENTITIES, Identity
from robot_persona.sprites import Expression

# Caps that keep speech equal between the robots (see the report: "the robot will speak when
# the player steals the ball, up to N times").
STEAL_LINES_MAX = 3
RESCUE_LINES_MAX = 3


@dataclass(frozen=True)
class VoiceTrigger:
    expression: Expression
    lines: list[str] = field(default_factory=list)
    chance: float = 1.0
    priority: int = 1
    max_per_round: int | None = None
    cooldown_s: float = 0.0


TRIGGERS: dict[str, VoiceTrigger] = {
    "introduction": VoiceTrigger(
        Expression.HAPPY,
        ["Hi, I'm {name}! I'm your teammate this round. My paddle is the {colour} one."],
        priority=3,
        max_per_round=1,
    ),
    "round_start": VoiceTrigger(
        Expression.EXCITED,
        ["Hi! Let's do this.", "Ready when you are!", "Okay, let's play!"],
        priority=3,
        max_per_round=1,
    ),
    "round_end": VoiceTrigger(
        Expression.HAPPY,
        ["That was fun!", "Good game!", "Well played!"],
        priority=3,
        max_per_round=1,
    ),
    "robot_brick": VoiceTrigger(
        Expression.HAPPY,
        ["Got one!", "Nice!", "Another brick down."],
        chance=0.2,
        cooldown_s=10,
    ),
    "human_brick": VoiceTrigger(
        Expression.HAPPY,
        ["Good shot!", "Nice one!", "Great hit!"],
        chance=0.15,
        cooldown_s=10,
    ),
    "human_steal": VoiceTrigger(
        Expression.SURPRISED,
        ["Oh, you took that one!", "Hey, I had that one!", "You took my ball!"],
        priority=2,
        max_per_round=STEAL_LINES_MAX,
    ),
    "human_rescue": VoiceTrigger(
        Expression.HAPPY,
        ["Thanks for the save!", "Phew, thank you!", "Nice save!"],
        priority=2,
        max_per_round=RESCUE_LINES_MAX,
    ),
    "human_prompted_rescue": VoiceTrigger(
        Expression.EXCITED,
        ["Thank you for helping!", "Thanks, you got it!"],
        priority=3,
        max_per_round=config.HELP_REQUESTS_PER_ROUND,
    ),
    "robot_steal": VoiceTrigger(
        Expression.EXCITED,
        ["I've got this one!", "Mine!", "Caught it!"],
        chance=0.5,
        priority=2,
        max_per_round=STEAL_LINES_MAX,
    ),
    "robot_rescue": VoiceTrigger(
        Expression.HAPPY,
        ["Got your ball!", "I saved it for you!", "Don't worry, I've got it!"],
        chance=0.5,
        priority=2,
        max_per_round=RESCUE_LINES_MAX,
    ),
    "help_request": VoiceTrigger(
        Expression.SURPRISED,
        ["Can you get that one?", "Help! I can't reach it!", "Quick, can you save that one?"],
        priority=3,
        max_per_round=config.HELP_REQUESTS_PER_ROUND,
    ),
    "help_missed": VoiceTrigger(
        Expression.SAD,
        ["Oh well, never mind.", "Ah, it got away."],
        priority=2,
        max_per_round=config.HELP_REQUESTS_PER_ROUND,
    ),
    "robot_lost": VoiceTrigger(
        Expression.SAD,
        ["Oops, missed it.", "Oh no!", "Sorry, that one got away."],
        chance=0.6,
        priority=2,
        cooldown_s=8,
    ),
    "human_lost": VoiceTrigger(
        Expression.SAD,
        ["So close!", "Unlucky!", "Almost had it."],
        chance=0.4,
        priority=2,
        cooldown_s=8,
    ),
    "powerup": VoiceTrigger(
        Expression.EXCITED,
        ["Extra ball!", "Ooh, a power-up!"],
        chance=0.8,
        priority=2,
    ),
    "idle": VoiceTrigger(
        Expression.NEUTRAL,
        ["Keep going!", "We're doing well.", "Watch the balls!"],
        priority=0,
    ),
}


def render(text: str, identity: Identity) -> str:
    return text.format(name=identity.name, colour=identity.colour_name)


def all_lines() -> list[tuple[str, str]]:
    """Every (trigger, text) pair as spoken by each robot, for the voice generator."""
    pairs = {
        (name, render(text, identity))
        for identity in IDENTITIES
        for name, t in TRIGGERS.items()
        for text in t.lines
    }
    return sorted(pairs)
