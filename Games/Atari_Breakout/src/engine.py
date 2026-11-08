"""Game loop: reads both players' actions, moves everything, and draws the frame."""

from typing import Any

import config
from entities import Ball, Brick, Paddle


class Game:
    def __init__(self) -> None:
        # Set up pygame, the window and clock, then the paddles, balls and bricks from config.
        self.human: Paddle
        self.robot: Paddle
        self.human_ball: Ball
        self.robot_ball: Ball
        self.bricks: list[Brick] = []
        self.score = 0
        self.lives = config.START_LIVES
        self.tick = 0
        self.message = ""
        raise NotImplementedError

    def _build_bricks(self) -> list[Brick]:
        """Lay out the brick grid from the BRICK_* values in config."""
        raise NotImplementedError

    def _observation_for_robot(self) -> dict[str, Any]:
        """Build the observation passed to robot_agent.get_robot_action()."""
        raise NotImplementedError

    def _apply_action(self, paddle: Paddle, action: str) -> None:
        """Move a paddle. Used for both players so they follow the same rules."""
        raise NotImplementedError

    def _can_bounce(self, paddle: Paddle, ball: Ball) -> bool:
        """Whether this paddle bounces this ball (see config.PADDLES_HIT_ANY_BALL)."""
        raise NotImplementedError

    def update(self) -> None:
        """One frame: human action, robot action (errors shown in the HUD), both balls,
        collisions."""
        raise NotImplementedError

    def draw(self) -> None:
        """Draw the HUD, bricks, both paddles and both balls, each in its owner's colour."""
        raise NotImplementedError

    def run(self) -> None:
        """Run the loop at config.FPS until the window closes or Esc is pressed."""
        raise NotImplementedError
