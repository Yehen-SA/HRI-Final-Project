"""Robot teammate. Tune the robot's skill with the values below.

Each frame the engine calls get_robot_action() with an observation dict and moves the
robot's paddle with the returned action, using the same movement rules as the human.
"""

from typing import Any

from actions import STAY

# --- Robot tuning ---
REACTION_DELAY_FRAMES = 6  # robot acts on what it saw this many frames ago
SPEED_FACTOR = 1.0  # fraction of frames the robot is allowed to move (1.0 = full speed)
AIM_ERROR_PX = 20  # random offset added to where the robot aims
DEADZONE_PX = 8  # don't move if already this close to the target
MISS_CHANCE = 0.0  # chance (0 to 1) the robot gives up on its ball
PREDICT_LANDING = True  # True: aim where its ball will land; False: follow the ball's x


def get_robot_action(observation: dict[str, Any]) -> str:
    """Pick the robot's action for this frame.

    observation keys:
      - tick: frame number
      - screen_width, screen_height
      - robot_ball: {"x", "y", "vx", "vy", "radius"}  (orange, the robot's own ball)
      - human_ball: {"x", "y", "vx", "vy", "radius"}  (blue, the human's ball)
      - paddles_hit_any_ball: whether the robot's paddle can also bounce the human's ball
      - robot_paddle: {"x", "y", "width"}
      - human_paddle: {"x", "y", "width"}
      - bricks_left, score, lives

    Returns one of actions.ACTIONS: "LEFT", "RIGHT" or "STAY".
    """
    return STAY
