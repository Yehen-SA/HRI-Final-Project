from collections import Counter

import assignment
import config
from robot_strategies import Strategy


def test_consecutive_ids_cover_every_cell_evenly() -> None:
    cells = Counter(
        (c.score_mode, tuple(c.robot_order))
        for c in (assignment.conditions_for(f"P{n:02d}") for n in range(1, 21))
    )
    assert len(cells) == 4
    assert set(cells.values()) == {5}


def test_score_mode_alternates_so_any_even_count_is_balanced() -> None:
    modes = [assignment.conditions_for(f"P{n}").score_mode for n in range(1, 7)]
    assert modes == ["shared", "split"] * 3


def test_id_number_parsing() -> None:
    assert assignment.id_number("P07") == 7
    assert assignment.id_number("pilot-12") == 12
    assert assignment.id_number("abc") == assignment.id_number("ABC")


def test_manual_assignments_and_override(monkeypatch) -> None:
    monkeypatch.setitem(
        assignment.MANUAL_ASSIGNMENTS, "X1", ("split", [Strategy.GOOD, Strategy.BAD])
    )
    c = assignment.conditions_for("X1")
    assert (c.score_mode, c.robot_order, c.assigned_by) == (
        "split",
        [Strategy.GOOD, Strategy.BAD],
        "manual",
    )
    monkeypatch.setattr(
        config, "CONDITION_OVERRIDE", {"score_mode": "shared", "robot_order": ["BAD", "GOOD"]}
    )
    c = assignment.conditions_for("X1")
    assert (c.score_mode, c.assigned_by) == ("shared", "override")
    assert c.as_log() == {
        "score_mode": "shared",
        "robot_order": ["BAD", "GOOD"],
        "assigned_by": "override",
    }
