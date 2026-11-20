"""The robot teammate.

Create one with a strategy from robot_strategies.py:

    robot = Robot(Strategy.GOOD)
    action = robot.get_action(observation)

Each frame the engine passes the observation (see robot_strategies.py for its keys) and moves
the robot's paddle with the returned action, using the same movement code as the human.
"""

import random

import config
from actions import LEFT, RIGHT
from robot_strategies import STRATEGIES, GoodStrategy, Observation, Strategy

# How close (px, beyond its own half-width) the robot lets its paddle get to where a ball it
# asked for help with will land, before moving away.
HELP_AVOID_MARGIN_PX = 30


class Robot:
    def __init__(self, strategy: Strategy, seed: int = config.SEED) -> None:
        self.strategy = strategy
        self.seed = seed
        self.reset()

    def reset(self) -> None:
        """Start fresh (same seed, so the same game gives the same robot moves)."""
        self._impl = STRATEGIES[self.strategy](random.Random(self.seed))

    def get_action(self, observation: Observation) -> str:
        """Pick this frame's action: one of actions.ACTIONS.

        Whatever the strategy, the robot moves out of the way of a ball it has asked the human
        to rescue, so both robots handle help requests the same way.
        """
        action = self._impl.act(observation)
        return self._avoid_help_requested_ball(observation) or action

    @staticmethod
    def _avoid_help_requested_ball(obs: Observation) -> str | None:
        paddle = obs["robot_paddle"]
        centre = paddle["x"] + paddle["width"] / 2
        for ball in obs["balls"]:
            if not ball.get("help_requested") or ball["waiting"] or ball["vy"] <= 0:
                continue
            _, land_x = GoodStrategy.landing_x(ball, obs["paddle_y"], obs["screen_width"])
            if abs(land_x - centre) < paddle["width"] / 2 + HELP_AVOID_MARGIN_PX:
                room_left = paddle["x"]
                room_right = obs["screen_width"] - (paddle["x"] + paddle["width"])
                if land_x >= centre:
                    return LEFT if room_left > 0 else RIGHT
                return RIGHT if room_right > 0 else LEFT
        return None
