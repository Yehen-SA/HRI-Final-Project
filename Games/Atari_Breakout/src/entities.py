"""Game objects: paddles, balls and bricks. Fields only for now."""

from dataclasses import dataclass

import pygame


@dataclass
class Paddle:
    owner: str  # "human" or "robot"
    x: float
    y: float
    width: int
    height: int

    def apply(self, action: str) -> None:
        """Move one frame according to `action`, staying on screen."""
        raise NotImplementedError


@dataclass
class Ball:
    owner: str  # "human" or "robot"; sets its colour and which paddle bounces it
    x: float
    y: float
    vx: float
    vy: float
    radius: int

    def step(self) -> None:
        """Move one frame along the current velocity."""
        raise NotImplementedError


@dataclass
class Brick:
    rect: pygame.Rect
    color: tuple[int, int, int]
    alive: bool = True
