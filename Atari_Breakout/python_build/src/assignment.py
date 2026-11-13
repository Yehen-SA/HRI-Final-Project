"""Which conditions each participant gets, decided by their participant ID.

Give each participant an ID such as P01, P02, P03... Only the number matters ("P07", "p7"
and "pilot-7" all count as 7). The number picks a row of CONDITION_CYCLE below, repeating every
four IDs:

    ID                          Score mode   Robot order
    P01  P05  P09  P13  P17     shared       BAD, then GOOD
    P02  P06  P10  P14  P18     split        BAD, then GOOD
    P03  P07  P11  P15  P19     shared       GOOD, then BAD
    P04  P08  P12  P16  P20     split        GOOD, then BAD

Handing out IDs in order keeps the groups balanced: P01-P20 gives 5 people per row, and 10 each
for shared and split.

To see the conditions for any range of IDs:

    uv run src/assignment.py 1 24

Two ways to override this, checked first:
  1. config.CONDITION_OVERRIDE: forces the same conditions for every ID (for piloting on our
     own devices). Set it back to None afterwards.
  2. MANUAL_ASSIGNMENTS below: give specific IDs specific conditions.

Every log records the conditions used and which of these three decided them.
"""

import re
import sys
from dataclasses import dataclass

import config
from robot_strategies import Strategy

GOOD, BAD = Strategy.GOOD, Strategy.BAD

# ID number 1 gets the first row, 2 the second, ... 5 the first again.
#   (score mode, robot order)
CONDITION_CYCLE: list[tuple[str, list[Strategy]]] = [
    ("shared", [BAD, GOOD]),  # P01, P05, P09, ...
    ("split", [BAD, GOOD]),  # P02, P06, P10, ...
    ("shared", [GOOD, BAD]),  # P03, P07, P11, ...
    ("split", [GOOD, BAD]),  # P04, P08, P12, ...
]

# Specific IDs with specific conditions; these win over the cycle. Example:
#   "P07": ("split", [GOOD, BAD]),
MANUAL_ASSIGNMENTS: dict[str, tuple[str, list[Strategy]]] = {}


@dataclass(frozen=True)
class Conditions:
    score_mode: str  # "shared" or "split"
    robot_order: list[Strategy]  # the robot in round 1, then round 2
    assigned_by: str  # "override", "manual" or "id number"

    def as_log(self) -> dict[str, object]:
        return {
            "score_mode": self.score_mode,
            "robot_order": [s.name for s in self.robot_order],
            "assigned_by": self.assigned_by,
        }


def id_number(participant_id: str) -> int:
    """The number in an ID: "P07" -> 7. (An ID with no digits gets a number from its letters.)"""
    digits = re.findall(r"\d+", participant_id)
    if digits:
        return int(digits[-1])
    return sum(ord(c) for c in participant_id.upper())


def conditions_for(participant_id: str) -> Conditions:
    """The conditions for this ID: override, then manual assignments, then the cycle."""
    override = config.CONDITION_OVERRIDE
    if override:
        order = [Strategy[name] for name in override["robot_order"]]
        return Conditions(override["score_mode"], order, "override")

    if participant_id in MANUAL_ASSIGNMENTS:
        mode, order = MANUAL_ASSIGNMENTS[participant_id]
        return Conditions(mode, list(order), "manual")

    row = (id_number(participant_id) - 1) % len(CONDITION_CYCLE)
    mode, order = CONDITION_CYCLE[row]
    return Conditions(mode, list(order), "id number")


if __name__ == "__main__":
    first, last = (int(a) for a in sys.argv[1:3]) if len(sys.argv) >= 3 else (1, 20)
    print(f"{'ID':<6}{'Score mode':<12}Robot order")
    for n in range(first, last + 1):
        pid = f"P{n:02d}"
        c = conditions_for(pid)
        print(f"{pid:<6}{c.score_mode:<12}{', then '.join(s.name for s in c.robot_order)}")
