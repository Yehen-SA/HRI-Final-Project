"""The robot teammate.

Create one with a strategy from robot_strategies.py:

    robot = Robot(Strategy.GOOD)
    action = robot.get_action(observation)

Each frame the engine passes the observation (see robot_strategies.py for its keys) and moves
the robot's paddle with the returned action, using the same movement code as the human.
"""

import random

import config
from robot_strategies import STRATEGIES, Observation, Strategy


class Robot:
    def __init__(self, strategy: Strategy, seed: int = config.SEED) -> None:
        self.strategy = strategy
        self.seed = seed
        self.reset()

    def reset(self) -> None:
        """Start fresh (same seed, so the same game gives the same robot moves)."""
        self._impl = STRATEGIES[self.strategy](random.Random(self.seed))

    def get_action(self, observation: Observation) -> str:
        """Pick this frame's action: one of actions.ACTIONS."""
        return self._impl.act(observation)
