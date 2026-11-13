"""Which conditions a participant gets, from their participant ID.

The two independent variables:
  - score mode (between subjects): "shared" or "split"
  - robot order (within subjects): BAD then GOOD, or GOOD then BAD

How it's decided, in order:
  1. config.CONDITION_OVERRIDE, if set (for our own devices / piloting).
  2. CONDITION_TABLE below, if the ID is listed.
  3. Otherwise from the number in the ID (P01, P02, ...): IDs cycle through CELLS, so every
     four consecutive IDs cover each combination once.
"""

import re
from dataclasses import dataclass

import config
from robot_strategies import Strategy

GOOD, BAD = Strategy.GOOD, Strategy.BAD

# The four combinations, in the order consecutive IDs get them (P01 -> first, P02 -> second...).
CELLS: list[tuple[str, list[Strategy]]] = [
    ("shared", [BAD, GOOD]),
    ("split", [BAD, GOOD]),
    ("shared", [GOOD, BAD]),
    ("split", [GOOD, BAD]),
]

# Optional explicit assignments, e.g. "P07": ("split", [GOOD, BAD]).
CONDITION_TABLE: dict[str, tuple[str, list[Strategy]]] = {}


@dataclass(frozen=True)
class Conditions:
    score_mode: str
    robot_order: list[Strategy]
    source: str  # "override", "table" or "id number": how they were decided

    def as_log(self) -> dict[str, object]:
        return {
            "score_mode": self.score_mode,
            "robot_order": [s.name for s in self.robot_order],
            "assigned_by": self.source,
        }


def id_number(participant_id: str) -> int:
    """The number in an ID ("P07" -> 7). IDs without digits fall back to a stable checksum."""
    digits = re.findall(r"\d+", participant_id)
    if digits:
        return int(digits[-1])
    return sum(ord(c) for c in participant_id.upper())


def conditions_for(participant_id: str) -> Conditions:
    override = config.CONDITION_OVERRIDE
    if override:
        order = [Strategy[name] for name in override["robot_order"]]
        return Conditions(override["score_mode"], order, "override")
    if participant_id in CONDITION_TABLE:
        mode, order = CONDITION_TABLE[participant_id]
        return Conditions(mode, list(order), "table")
    mode, order = CELLS[(id_number(participant_id) - 1) % len(CELLS)]
    return Conditions(mode, list(order), "id number")
