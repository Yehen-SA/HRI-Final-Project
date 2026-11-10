import config
import robot_agent
from actions import ACTIONS, LEFT, RIGHT


def obs(x: float, last: str) -> dict:
    return {
        "screen_width": config.SCREEN_WIDTH,
        "robot_paddle": {"x": x, "y": config.PADDLE_Y, "width": config.PADDLE_WIDTH},
        "robot_last_action": last,
    }


def test_returns_a_valid_action() -> None:
    assert robot_agent.get_robot_action(obs(300, RIGHT)) in ACTIONS


def test_keeps_going_the_same_way_mid_screen() -> None:
    assert robot_agent.get_robot_action(obs(300, RIGHT)) == RIGHT
    assert robot_agent.get_robot_action(obs(300, LEFT)) == LEFT


def test_turns_at_both_edges() -> None:
    right_edge = config.SCREEN_WIDTH - config.PADDLE_WIDTH
    assert robot_agent.get_robot_action(obs(right_edge, RIGHT)) == LEFT
    assert robot_agent.get_robot_action(obs(0, LEFT)) == RIGHT
