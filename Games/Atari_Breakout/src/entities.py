"""Game objects: paddles, balls and bricks."""

from dataclasses import dataclass

import pygame

from actions import LEFT, RIGHT


@dataclass
class Paddle:
    owner: str  # "human" or "robot"
    x: float  # left edge
    y: float  # top edge
    width: int
    height: int
    speed: float  # pixels per frame
    screen_width: int

    @property
    def centre_x(self) -> float:
        return self.x + self.width / 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def apply(self, action: str) -> None:
        """Move one frame according to `action`, staying on screen."""
        if action == LEFT:
            self.x -= self.speed
        elif action == RIGHT:
            self.x += self.speed
        self.x = max(0.0, min(self.x, self.screen_width - self.width))


@dataclass
class Ball:
    owner: str  # "human" or "robot": who scores its next brick; also its colour
    x: float  # centre
    y: float
    vx: float
    vy: float
    radius: int
    waiting: bool = True  # sitting on its owner's paddle, not yet launched
    launch_tick: int = 0  # robot's waiting balls: the frame they launch by themselves
    id: int = 0  # stable number so the robot can tell balls apart

    @property
    def rect(self) -> pygame.Rect:
        r = self.radius
        return pygame.Rect(round(self.x - r), round(self.y - r), 2 * r, 2 * r)

    def step(self) -> None:
        """Move one frame along the current velocity."""
        self.x += self.vx
        self.y += self.vy


@dataclass
class Brick:
    rect: pygame.Rect
    color: tuple[int, int, int]
    row: int  # 0 is the top row
    points: int
    alive: bool = True
