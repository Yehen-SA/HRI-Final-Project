"""Robot teammate.

Basic version: the robot ignores the balls and sweeps its paddle left and right across the
whole screen, turning at each edge. Its speed is ROBOT_PADDLE_SPEED in config.py.
Skill presets (poor / average / good) replace this in a later phase; see docs/plan.md.

Each frame the engine calls get_robot_action() with an observation dict and moves the
robot's paddle with the returned action.
"""

from typing import Any

from actions import LEFT, RIGHT


def get_robot_action(observation: dict[str, Any]) -> str:
    """Pick the robot's action for this frame.

    observation keys:
      - tick: frame number
      - screen_width, screen_height
      - robot_ball, human_ball: {"x", "y", "vx", "vy", "radius", "waiting"}
      - paddles_hit_any_ball: whether the robot's paddle can also bounce the human's ball
      - robot_paddle, human_paddle: {"x", "y", "width"}
      - robot_last_action: the robot's action last frame
      - bricks_left

    Returns one of actions.ACTIONS: "LEFT", "RIGHT" or "STAY".
    """
    paddle = observation["robot_paddle"]
    if paddle["x"] <= 0:
        return RIGHT
    if paddle["x"] + paddle["width"] >= observation["screen_width"]:
        return LEFT
    return LEFT if observation.get("robot_last_action") == LEFT else RIGHT
