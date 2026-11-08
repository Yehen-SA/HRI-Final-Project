import robot_agent
from actions import ACTIONS


def test_returns_a_valid_action() -> None:
    assert robot_agent.get_robot_action({}) in ACTIONS


def test_tuning_values_in_range() -> None:
    assert robot_agent.REACTION_DELAY_FRAMES >= 0
    assert 0 < robot_agent.SPEED_FACTOR <= 1
    assert robot_agent.AIM_ERROR_PX >= 0
    assert robot_agent.DEADZONE_PX >= 0
    assert 0 <= robot_agent.MISS_CHANCE <= 1
