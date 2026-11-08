"""Human player input: keyboard to action. Nothing robot-related lives here."""

from collections.abc import Sequence

import pygame

from actions import LEFT, RIGHT

KEY_BINDINGS = {
    pygame.K_a: LEFT,
    pygame.K_LEFT: LEFT,
    pygame.K_d: RIGHT,
    pygame.K_RIGHT: RIGHT,
}

QUIT_KEY = pygame.K_ESCAPE


def read_human_action(pressed: Sequence[bool]) -> str:
    """Turn the currently held keys (from pygame.key.get_pressed()) into one action."""
    raise NotImplementedError
