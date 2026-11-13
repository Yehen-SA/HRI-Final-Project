import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import config
from engine import ROBOT, Game
from robot_persona import Expression, RobotPersona, sprites
from robot_persona import persona_config as cfg
from robot_persona.lines import TRIGGERS, all_lines
from robot_persona.speech import Speech, voice_path
from robot_strategies import Strategy


@pytest.fixture(autouse=True)
def _pygame():
    # Started once and left running: fonts are cached (ui.font) and break after pygame.quit().
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))


def test_every_trigger_has_lines_and_a_valid_expression() -> None:
    for name, trigger in TRIGGERS.items():
        assert trigger.lines, name
        assert isinstance(trigger.expression, Expression)
        assert 0 <= trigger.chance <= 1


def test_every_line_has_a_voice_file() -> None:
    missing = [text for t, text in all_lines() if not voice_path(t, text).exists()]
    assert not missing, f"run `uv run tools/generate_voice.py` for: {missing}"


def test_auto_uses_procedural_without_a_full_set_of_images(monkeypatch) -> None:
    monkeypatch.setattr(sprites, "images_available", lambda name="": False)
    assert isinstance(sprites.make_sprite("auto"), sprites.ProceduralSprite)


def test_auto_switches_to_images_when_all_are_present(tmp_path, monkeypatch) -> None:
    for e in Expression:
        surf = pygame.Surface((10, 10))
        pygame.image.save(surf, str(tmp_path / f"{e.value}.png"))
    monkeypatch.setattr(sprites, "image_path", lambda e, name="": tmp_path / f"{e.value}.png")
    sprite = sprites.make_sprite("auto")
    assert isinstance(sprite, sprites.ImageSprite)
    sprite.draw(pygame.display.get_surface(), pygame.Rect(0, 0, 84, 100), Expression.HAPPY, False)


def test_bad_sprite_source_is_rejected() -> None:
    with pytest.raises(ValueError):
        sprites.make_sprite("cartoon")


def test_every_expression_draws() -> None:
    surface = pygame.display.get_surface()
    sprite = sprites.ProceduralSprite()
    for e in Expression:
        for blink in (False, True):
            sprite.draw(surface, pygame.Rect(100, 600, 84, 100), e, blink)


def test_speech_cooldown_and_priority() -> None:
    speech = Speech()
    assert speech.can_say(1, now=0)
    speech.say("robot_brick", "Nice!", 1, now=0)
    assert not speech.can_say(1, now=1)  # bubble still showing, same priority
    assert speech.can_say(2, now=1)  # higher priority interrupts
    assert not speech.can_say(1, now=cfg.BUBBLE_SECONDS + 0.1)  # bubble gone, still cooling down
    assert speech.can_say(1, now=cfg.SPEECH_COOLDOWN_S + 0.1)
    assert speech.can_say(3, now=cfg.BUBBLE_SECONDS + 0.1)  # top priority skips the cooldown


def test_missing_voice_file_is_silent(monkeypatch, tmp_path) -> None:
    import robot_persona.speech as speech_module

    monkeypatch.setattr(speech_module, "voice_path", lambda t, text: tmp_path / "none.ogg")
    Speech().say("idle", "Not recorded", 0, now=0)


def test_reacts_to_game_events_and_logs_what_it_says() -> None:
    said = []
    persona = RobotPersona(on_say=lambda trigger, text: said.append(trigger))
    game = Game(robot_strategy=Strategy.SWEEP, rules=[], listeners=[persona])
    assert said == ["round_start"]  # always greets
    assert persona.expression is Expression.EXCITED
    ball = next(b for b in game.balls if b.owner == ROBOT)
    ball.waiting, ball.x, ball.y, ball.vy = False, 50, config.PLAY_BOTTOM + 20, 3
    game.update()
    persona.update(game)
    assert persona.expression is Expression.SAD
    for _ in range(round(cfg.EXPRESSION_SECONDS * config.FPS) + 1):
        persona.update(game)
    assert persona.expression in (Expression.NEUTRAL, Expression.FOCUSED)


def test_says_an_idle_line_after_a_quiet_spell() -> None:
    said = []
    persona = RobotPersona(on_say=lambda trigger, text: said.append(trigger))
    game = Game(robot_strategy=Strategy.SWEEP, rules=[], listeners=[persona])
    for _ in range(round((cfg.IDLE_LINE_AFTER_S + 1) * config.FPS)):
        persona.update(game)
    assert said.count("idle") == 1


def test_persona_draws_under_the_robot_paddle() -> None:
    persona = RobotPersona()
    game = Game(robot_strategy=Strategy.SWEEP, rules=[], listeners=[persona])
    rect = persona.sprite_rect(game.robot.rect)
    assert rect.centerx == game.robot.rect.centerx
    assert rect.top >= config.PLAY_BOTTOM and rect.bottom <= config.SCREEN_HEIGHT
    persona.draw(pygame.display.get_surface(), game.robot.rect)


def test_two_robot_identities_with_different_names_and_colours() -> None:
    first, second = cfg.identity_for_round(1), cfg.identity_for_round(2)
    assert (first.name, second.name) == ("Nova", "Pip")
    assert first.body != second.body
    assert config.COLOR_HUMAN not in (first.body, second.body)


def test_persona_uses_its_identity() -> None:
    pip = cfg.identity_for_round(2)
    persona = RobotPersona(identity=pip)
    assert persona.identity.name == "Pip"
    assert persona.sprite.body_colour == pip.body


def test_per_robot_images_are_preferred(tmp_path, monkeypatch) -> None:
    import paths

    monkeypatch.setattr(paths, "game_dir", lambda: tmp_path)
    (tmp_path / "assets" / "robot" / "pip").mkdir(parents=True)
    (tmp_path / "assets" / "robot" / "pip" / "happy.png").write_bytes(b"")
    assert sprites.image_path(Expression.HAPPY, "Pip").parent.name == "pip"
    assert sprites.image_path(Expression.HAPPY, "Nova").parent.name == "robot"
