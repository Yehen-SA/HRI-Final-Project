"""RobotPersona: the robot as a character, sitting under its paddle and reacting to the game.

Use it as a game listener, then update and draw it each frame:

    persona = RobotPersona(on_say=lambda trigger, text: ...)
    game = Game(listeners=[persona])
    ...
    persona.update(game)
    persona.draw(surface, game.robot.rect)

It reacts to the same events for every strategy and score mode: its face shows a reaction for
a moment (happy, sad, surprised...), then goes back to neutral, or "focused" while a ball is
coming down. Sometimes it also says a line (lines.py).
"""

import random
from collections.abc import Callable
from typing import Any

import pygame

import config
import ui
from robot_persona import persona_config as cfg
from robot_persona.lines import TRIGGERS
from robot_persona.speech import Speech
from robot_persona.sprites import Expression, ImageSprite, ProceduralSprite, make_sprite

SayCallback = Callable[[str, str], None]  # (trigger, text)


class RobotPersona:
    def __init__(
        self,
        on_say: SayCallback | None = None,
        seed: int = config.SEED,
        sprite: ProceduralSprite | ImageSprite | None = None,
    ) -> None:
        self.on_say = on_say
        self.rng = random.Random(seed + cfg.SEED_OFFSET)
        self.sprite = sprite or make_sprite()
        self.speech = Speech()
        self.frames = 0
        self.reaction: Expression | None = None
        self.reaction_until = 0.0
        self.idle_expression = Expression.NEUTRAL
        self.next_blink = self._blink_gap()
        self.blink_until = 0.0
        self.game_over = False
        self._last_idle = 0.0
        self._last_line: dict[str, str] = {}

    @property
    def now(self) -> float:
        return self.frames / config.FPS

    @property
    def expression(self) -> Expression:
        if self.reaction is not None and self.now < self.reaction_until:
            return self.reaction
        return self.idle_expression

    # --- Reacting to the game ---

    def __call__(self, game: Any, event: str, data: dict[str, Any]) -> None:
        trigger = self._trigger_for(event, data)
        if trigger:
            self.react(trigger)
        if event == "round_end":
            self.game_over = True

    @staticmethod
    def _trigger_for(event: str, data: dict[str, Any]) -> str | None:
        if event == "round_start":
            return "round_start"
        if event == "round_end":
            return "round_end"
        if event == "brick_broken":
            return "robot_brick" if data["ball"].owner == "robot" else "human_brick"
        if event == "steal":
            return "robot_steal" if data["paddle"].owner == "robot" else "human_steal"
        if event == "ball_lost":
            return "robot_lost" if data["ball"].owner == "robot" else "human_lost"
        if event == "powerup_caught":
            return "powerup"
        return None

    def react(self, trigger: str) -> None:
        """Show the trigger's expression, and maybe say one of its lines."""
        t = TRIGGERS[trigger]
        self.reaction = t.expression
        self.reaction_until = self.now + cfg.EXPRESSION_SECONDS
        if t.lines and self.rng.random() < t.chance and self.speech.can_say(t.priority, self.now):
            options = [line for line in t.lines if line != self._last_line.get(trigger)] or t.lines
            text = self.rng.choice(options)
            self._last_line[trigger] = text
            self.speech.say(trigger, text, t.priority, self.now)
            if self.on_say:
                self.on_say(trigger, text)

    # --- Every frame ---

    def update(self, game: Any) -> None:
        self.frames += 1
        falling = any(
            not b.waiting and b.vy > 0 and b.y > config.PLAY_BOTTOM * 0.55 for b in game.balls
        )
        self.idle_expression = Expression.FOCUSED if falling else Expression.NEUTRAL
        if self.now >= self.next_blink:
            self.blink_until = self.now + 0.15
            self.next_blink = self.now + self._blink_gap()
        quiet_for = self.now - max(self.speech.last_spoke_at, self._last_idle)
        if not self.game_over and quiet_for >= cfg.IDLE_LINE_AFTER_S:
            self._last_idle = self.now
            self.react("idle")

    def _blink_gap(self) -> float:
        return self.rng.uniform(*cfg.BLINK_EVERY_S)

    def stop(self) -> None:
        """Stop any voice line (e.g. when leaving the round)."""
        self.speech.stop()

    # --- Drawing ---

    def sprite_rect(self, paddle_rect: pygame.Rect) -> pygame.Rect:
        rect = pygame.Rect(0, 0, cfg.SPRITE_WIDTH, cfg.SPRITE_HEIGHT)
        rect.midtop = (paddle_rect.centerx, config.PLAY_BOTTOM + 4)
        return rect

    def draw(self, surface: pygame.Surface, paddle_rect: pygame.Rect) -> None:
        """Draw the robot under its paddle, holding it up with two arms, plus any speech."""
        rect = self.sprite_rect(paddle_rect)
        shoulder_y = rect.top + rect.height // 3
        for side in (-1, 1):
            shoulder = (rect.centerx + side * (rect.width // 2 - 4), shoulder_y)
            hand = (paddle_rect.centerx + side * (paddle_rect.width // 2 - 12), paddle_rect.bottom)
            pygame.draw.line(surface, cfg.TRIM_COLOR, shoulder, hand, 4)
            pygame.draw.circle(surface, cfg.TRIM_COLOR, hand, 4)
        self.sprite.draw(surface, rect, self.expression, self.now < self.blink_until)

        name = ui.font(20).render(cfg.NAME, True, (170, 175, 190))
        side_x = (
            rect.right + 8
            if rect.right + 8 + name.get_width() < surface.get_width()
            else (rect.left - 8 - name.get_width())
        )
        surface.blit(name, (side_x, rect.bottom - name.get_height()))

        line = self.speech.visible_line(self.now)
        if line:
            self.speech.draw_bubble(surface, rect, line.text)
