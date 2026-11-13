"""Small drawing helpers shared by the session screens: fonts, wrapped text and buttons."""

from functools import cache

import pygame

import config


@cache
def font(size: int) -> pygame.font.Font:
    return pygame.font.Font(None, size)


def wrap(text: str, size: int, width: int) -> list[str]:
    """Split text into lines that fit `width` pixels. Blank lines in the text are kept."""
    f = font(size)
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            if f.size(f"{line} {word}")[0] <= width:
                line = f"{line} {word}"
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_text_block(
    surface: pygame.Surface,
    text: str,
    size: int,
    x: int,
    y: int,
    width: int,
    color: tuple[int, int, int] = config.COLOR_TEXT,
    center: bool = False,
) -> int:
    """Draw wrapped text; returns the y just below it."""
    f = font(size)
    line_height = f.get_linesize()
    for line in wrap(text, size, width):
        surf = f.render(line, True, color)
        lx = x + (width - surf.get_width()) // 2 if center else x
        surface.blit(surf, (lx, y))
        y += line_height
    return y


def draw_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    selected: bool = False,
    enabled: bool = True,
    size: int = 26,
) -> None:
    if not enabled:
        fill, text = config.COLOR_HUD, (110, 110, 120)
    elif selected:
        fill, text = config.COLOR_HUMAN, config.COLOR_TEXT
    else:
        fill, text = (52, 58, 76), config.COLOR_TEXT
    pygame.draw.rect(surface, fill, rect, border_radius=6)
    if selected:
        pygame.draw.rect(surface, config.COLOR_TEXT, rect, width=2, border_radius=6)
    surf = font(size).render(label, True, text)
    surface.blit(surf, surf.get_rect(center=rect.center))


def draw_overlay(surface: pygame.Surface, lines: list[str], alpha: int = 190) -> None:
    """Dim the screen and show centred lines of text (pause and end-of-round messages)."""
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, alpha))
    surface.blit(shade, (0, 0))
    f = font(34)
    total = len(lines) * f.get_linesize()
    y = (surface.get_height() - total) // 2
    for line in lines:
        surf = f.render(line, True, config.COLOR_TEXT)
        surface.blit(surf, ((surface.get_width() - surf.get_width()) // 2, y))
        y += f.get_linesize()
