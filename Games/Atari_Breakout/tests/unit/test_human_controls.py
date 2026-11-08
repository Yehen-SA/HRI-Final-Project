from actions import ACTIONS
from human_controls import KEY_BINDINGS, QUIT_KEY


def test_every_binding_is_a_valid_action() -> None:
    assert KEY_BINDINGS
    assert all(action in ACTIONS for action in KEY_BINDINGS.values())


def test_quit_key_is_not_bound_to_movement() -> None:
    assert QUIT_KEY not in KEY_BINDINGS
