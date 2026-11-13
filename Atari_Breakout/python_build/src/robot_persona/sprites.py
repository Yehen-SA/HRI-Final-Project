"""How the robot looks: one picture per expression.

Two interchangeable sprite sources, picked by persona_config.SPRITE_SOURCE:
  - ProceduralSprite draws a robot head and body with pygame shapes (no image files needed).
  - ImageSprite uses assets/robot/<expression>.png, e.g. assets/robot/happy.png.
    Images are scaled to SPRITE_WIDTH x SPRITE_HEIGHT.

With "auto", images are used as soon as there's one for every expression, so swapping the art
in is just a matter of dropping the files in. Each robot looks in assets/robot/<name>/ first
(e.g. assets/robot/nova/), then in assets/robot/.
"""

import math
from enum import Enum

import pygame

import paths
from robot_persona import persona_config as cfg


class Expression(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    SURPRISED = "surprised"
    FOCUSED = "focused"
    EXCITED = "excited"


def image_path(expression: Expression, name: str = ""):
    """assets/robot/<name>/<expression>.png if it exists, else assets/robot/<expression>.png."""
    own = paths.asset("robot", name.lower(), f"{expression.value}.png")
    if name and own.exists():
        return own
    return paths.asset("robot", f"{expression.value}.png")


class ProceduralSprite:
    """A friendly robot drawn in code: antenna, screen face with eyes and mouth, small body."""

    def __init__(self, identity: cfg.Identity = cfg.FREE_PLAY_IDENTITY) -> None:
        self.body_colour = identity.body
        self.trim_colour = identity.trim

    def draw(
        self, surface: pygame.Surface, rect: pygame.Rect, expression: Expression, blink: bool
    ) -> None:
        w, h = rect.width, rect.height
        head = pygame.Rect(0, 0, w, round(h * 0.56))
        head.midtop = (rect.centerx, rect.top + round(h * 0.08))
        body = pygame.Rect(0, 0, round(w * 0.64), round(h * 0.34))
        body.midtop = (rect.centerx, head.bottom - 2)

        # Antenna
        tip = (rect.centerx, rect.top + 2)
        pygame.draw.line(surface, self.trim_colour, tip, (rect.centerx, head.top), 3)
        pygame.draw.circle(surface, cfg.EYE_COLOR, tip, 4)
        # Body with a chest light
        pygame.draw.rect(surface, self.trim_colour, body, border_radius=8)
        light = (
            cfg.EYE_COLOR
            if expression in (Expression.HAPPY, Expression.EXCITED)
            else (90, 100, 120)
        )
        pygame.draw.circle(surface, light, body.center, max(3, w // 14))
        # Head and face screen
        pygame.draw.rect(surface, self.body_colour, head, border_radius=12)
        face = head.inflate(-round(w * 0.18), -round(head.height * 0.26))
        pygame.draw.rect(surface, cfg.FACE_COLOR, face, border_radius=8)
        # Ears
        for side in (-1, 1):
            ear = pygame.Rect(0, 0, 6, head.height // 3)
            ear.center = (head.centerx + side * (head.width // 2 + 2), head.centery)
            pygame.draw.rect(surface, self.trim_colour, ear, border_radius=3)

        self._draw_face(surface, face, expression, blink)

    def _draw_face(
        self, surface: pygame.Surface, face: pygame.Rect, expression: Expression, blink: bool
    ) -> None:
        eye = cfg.EYE_COLOR
        r = max(3, face.height // 6)
        eye_y = face.top + round(face.height * 0.4)
        eyes = [(face.centerx - face.width // 4, eye_y), (face.centerx + face.width // 4, eye_y)]
        mouth_y = face.top + round(face.height * 0.75)
        mw = face.width // 3

        for x, y in eyes:
            if blink and expression is not Expression.SURPRISED:
                pygame.draw.line(surface, eye, (x - r, y), (x + r, y), 2)
            elif expression is Expression.HAPPY or expression is Expression.EXCITED:
                arc = pygame.Rect(x - r, y - r, 2 * r, 2 * r)
                pygame.draw.arc(surface, eye, arc, 0, math.pi, 3)  # ^ ^ eyes
            elif expression is Expression.SAD:
                pygame.draw.circle(surface, eye, (x, y + 2), r - 1)
                inner = -1 if x < face.centerx else 1  # inner ends raised: worried, not angry
                pygame.draw.line(
                    surface, eye, (x - r, y - r - 2 - inner * 3), (x + r, y - r - 2 + inner * 3), 2
                )
            elif expression is Expression.SURPRISED:
                pygame.draw.circle(surface, eye, (x, y), r + 2, 2)
                pygame.draw.circle(surface, eye, (x, y), 2)
            elif expression is Expression.FOCUSED:
                pygame.draw.rect(surface, eye, (x - r, y - 2, 2 * r, 4), border_radius=2)
            else:
                pygame.draw.circle(surface, eye, (x, y), r)

        mouth = pygame.Rect(face.centerx - mw // 2, mouth_y - 6, mw, 12)
        if expression is Expression.HAPPY:
            pygame.draw.arc(surface, eye, mouth, math.pi, 2 * math.pi, 3)
        elif expression is Expression.EXCITED:
            pygame.draw.ellipse(surface, eye, mouth.inflate(0, 2))
        elif expression is Expression.SAD:
            pygame.draw.arc(surface, eye, mouth.move(0, 6), 0, math.pi, 3)
        elif expression is Expression.SURPRISED:
            pygame.draw.circle(surface, eye, mouth.center, 5, 2)
        else:
            width = mw // 2 if expression is Expression.FOCUSED else mw
            pygame.draw.line(
                surface,
                eye,
                (face.centerx - width // 2, mouth_y),
                (face.centerx + width // 2, mouth_y),
                3,
            )


class ImageSprite:
    """Draws assets/robot/<expression>.png, scaled to the sprite size."""

    def __init__(self, identity: cfg.Identity = cfg.FREE_PLAY_IDENTITY) -> None:
        size = (cfg.SPRITE_WIDTH, cfg.SPRITE_HEIGHT)
        self.images = {
            e: pygame.transform.smoothscale(
                pygame.image.load(str(image_path(e, identity.name))), size
            )
            for e in Expression
        }

    def draw(
        self, surface: pygame.Surface, rect: pygame.Rect, expression: Expression, blink: bool
    ) -> None:
        surface.blit(self.images[expression], rect)


def images_available(name: str = "") -> bool:
    return all(image_path(e, name).exists() for e in Expression)


def make_sprite(
    source: str = cfg.SPRITE_SOURCE, identity: cfg.Identity = cfg.FREE_PLAY_IDENTITY
) -> ProceduralSprite | ImageSprite:
    """Pick the sprite source: "auto", "procedural" or "images"."""
    if source == "images" or (source == "auto" and images_available(identity.name)):
        return ImageSprite(identity)
    if source not in ("auto", "procedural"):
        raise ValueError(f"SPRITE_SOURCE must be 'auto', 'procedural' or 'images', not {source!r}")
    return ProceduralSprite(identity)
