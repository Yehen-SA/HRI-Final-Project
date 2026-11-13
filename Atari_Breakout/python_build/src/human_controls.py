"""Human player input: keyboard to action. Nothing robot-related lives here."""

from collections.abc import Callable

import pygame

from actions import LEFT, RIGHT, STAY

KEY_BINDINGS = {
    pygame.K_a: LEFT,
    pygame.K_LEFT: LEFT,
    pygame.K_d: RIGHT,
    pygame.K_RIGHT: RIGHT,
}

LAUNCH_KEY = pygame.K_SPACE  # launches the human's ball; also "play again" after game over
QUIT_KEY = pygame.K_ESCAPE


def read_human_action(is_pressed: Callable[[int], bool]) -> str:
    """Turn the currently held keys into one action.

    `is_pressed(key)` says whether a key is held; in the game it's
    `pygame.key.get_pressed().__getitem__`. Holding both directions (or neither) is STAY.
    """
    left = any(is_pressed(k) for k, a in KEY_BINDINGS.items() if a == LEFT)
    right = any(is_pressed(k) for k, a in KEY_BINDINGS.items() if a == RIGHT)
    if left == right:
        return STAY
    return LEFT if left else RIGHT
