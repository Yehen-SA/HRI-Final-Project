import pygame

from actions import ACTIONS, LEFT, RIGHT, STAY
from human_controls import KEY_BINDINGS, LAUNCH_KEY, QUIT_KEY, read_human_action


def held(*keys: int):
    return lambda key: key in keys


def test_every_binding_is_a_valid_action() -> None:
    assert KEY_BINDINGS
    assert all(action in ACTIONS for action in KEY_BINDINGS.values())


def test_quit_and_launch_keys_are_not_bound_to_movement() -> None:
    assert QUIT_KEY not in KEY_BINDINGS
    assert LAUNCH_KEY not in KEY_BINDINGS


def test_keys_to_action() -> None:
    assert read_human_action(held()) == STAY
    assert read_human_action(held(pygame.K_a)) == LEFT
    assert read_human_action(held(pygame.K_RIGHT)) == RIGHT
    assert read_human_action(held(pygame.K_a, pygame.K_d)) == STAY
