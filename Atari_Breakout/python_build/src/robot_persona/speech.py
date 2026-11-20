"""Speech bubbles and voice playback.

A line is shown in a bubble beside the robot (never over the play area) and, if a matching
voice file exists, played aloud. Voice files are named after the line's text, so editing a
line just needs `uv run tools/generate_voice.py` to make the new file.
"""

import hashlib
from dataclasses import dataclass

import pygame

import paths
import ui
from robot_persona import persona_config as cfg


def voice_file_name(trigger: str, text: str) -> str:
    """e.g. "robot_steal_1a2b3c4d.ogg": the trigger plus a hash of the text and voice."""
    digest = hashlib.sha1(f"{cfg.PIPER_VOICE}|{text}".encode()).hexdigest()[:8]
    return f"{trigger}_{digest}.ogg"


def voice_path(trigger: str, text: str):
    return paths.asset("robot", "voice", voice_file_name(trigger, text))


@dataclass
class SpokenLine:
    trigger: str
    text: str
    priority: int
    until: float  # seconds (game clock) when the bubble disappears


class Speech:
    """Shows one line at a time with a cooldown; higher priority lines can interrupt."""

    def __init__(self) -> None:
        self.current: SpokenLine | None = None
        self.last_spoke_at = -1e9
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._channel: pygame.mixer.Channel | None = None
        self._audio_ok = cfg.VOICE_ENABLED and _init_audio()

    def can_say(self, priority: int, now: float) -> bool:
        """While a bubble shows, only a higher-priority line may interrupt it. Otherwise wait
        for the cooldown, except for top-priority lines (round start and end)."""
        if not cfg.SPEECH_ENABLED:
            return False
        if self.visible_line(now):
            return priority > self.current.priority
        return priority >= 3 or now - self.last_spoke_at >= cfg.SPEECH_COOLDOWN_S

    def say(self, trigger: str, text: str, priority: int, now: float, hold: bool = False) -> None:
        """Show and play a line. `hold`: keep the bubble up until clear() is called."""
        until = float("inf") if hold else now + cfg.BUBBLE_SECONDS
        self.current = SpokenLine(trigger, text, priority, until)
        self.last_spoke_at = now
        self._play(trigger, text)

    def clear(self) -> None:
        """Take the bubble down (the voice line, if playing, finishes)."""
        self.current = None

    def visible_line(self, now: float) -> SpokenLine | None:
        if self.current and now < self.current.until:
            return self.current
        return None

    # --- Voice ---

    def _play(self, trigger: str, text: str) -> None:
        if not self._audio_ok:
            return
        path = voice_path(trigger, text)
        key = str(path)
        if key not in self._sounds:
            try:
                sound = pygame.mixer.Sound(key) if path.exists() else None
            except pygame.error:
                sound = None
            if sound is not None:
                sound.set_volume(cfg.VOICE_VOLUME)
            self._sounds[key] = sound
        sound = self._sounds[key]
        if sound is None:
            return
        if self._channel is not None:
            self._channel.stop()
        self._channel = sound.play()

    def stop(self) -> None:
        if self._channel is not None:
            self._channel.stop()

    # --- Drawing ---

    def draw_bubble(self, surface: pygame.Surface, robot_rect: pygame.Rect, text: str) -> None:
        """A rounded bubble beside the robot, on whichever side has more room."""
        size = cfg.BUBBLE_TEXT_SIZE
        lines = ui.wrap(text, size, cfg.BUBBLE_MAX_WIDTH)
        font = ui.font(size)
        width = max(font.size(line)[0] for line in lines) + 24
        height = len(lines) * font.get_linesize() + 16
        gap = 16
        room_right = surface.get_width() - robot_rect.right
        bubble = pygame.Rect(0, 0, width, height)
        bubble.centery = robot_rect.top + robot_rect.height // 3
        if room_right >= width + gap or room_right >= robot_rect.left:
            bubble.left = robot_rect.right + gap
            tail = [
                (bubble.left, bubble.centery - 6),
                (bubble.left, bubble.centery + 6),
                (robot_rect.right + 2, bubble.centery),
            ]
        else:
            bubble.right = robot_rect.left - gap
            tail = [
                (bubble.right, bubble.centery - 6),
                (bubble.right, bubble.centery + 6),
                (robot_rect.left - 2, bubble.centery),
            ]
        bubble.clamp_ip(surface.get_rect())
        fill, ink = (245, 245, 250), (25, 28, 38)
        pygame.draw.polygon(surface, fill, tail)
        pygame.draw.rect(surface, fill, bubble, border_radius=10)
        y = bubble.top + 8
        for line in lines:
            surf = font.render(line, True, ink)
            surface.blit(surf, (bubble.left + 12, y))
            y += font.get_linesize()


def _init_audio() -> bool:
    """Start the mixer if there's an audio device; play silently otherwise."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return True
    except pygame.error:
        return False
