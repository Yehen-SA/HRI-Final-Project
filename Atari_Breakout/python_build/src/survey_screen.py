"""The survey screen: shows a list of questions (questions.py) one page at a time.

Mouse or keyboard: click an option or press its number, Enter for Next, arrow keys move a
slider, type into text boxes. Back returns to the previous question. Next stays disabled until
a required question is answered (sliders must be moved at least once).
"""

from typing import Any

import pygame

import config
import ui
from questions import (
    Consent,
    Context,
    Info,
    Likert,
    MultipleChoice,
    Question,
    Slider,
    TextAnswer,
    visible_questions,
)
from session_log import Answer

MARGIN = 60
WIDTH = config.SCREEN_WIDTH - 2 * MARGIN
TEXT_SIZE = 32
OPTION_HEIGHT = 40
BUTTON_W, BUTTON_H = 160, 46


class SurveyScreen:
    def __init__(self, title: str, questions: list[Question], context: Context) -> None:
        self.title = title
        self.context = context
        self.questions = visible_questions(questions, context)
        self.values: dict[str, Any] = {}
        self.index = 0
        self.done = not self.questions
        self.declined = False  # a Consent question was declined
        self._dragging = False

    # --- State ---

    @property
    def question(self) -> Question:
        return self.questions[self.index]

    def can_continue(self) -> bool:
        q = self.question
        if isinstance(q, Consent):
            return False  # answered with its own buttons
        return not q.required or q.is_answered(self.values.get(q.id))

    def next(self) -> None:
        if not self.can_continue():
            return
        self.index += 1
        if self.index >= len(self.questions):
            self.index = len(self.questions) - 1
            self.done = True

    def back(self) -> None:
        self.index = max(0, self.index - 1)

    def answers(self) -> list[Answer]:
        """Answers in question order, for the log (Info pages are left out)."""
        return [
            Answer(q.id, q.render_text(self.context), self.values.get(q.id))
            for q in self.questions
            if q.logged
        ]

    def auto_answer(self) -> None:
        """Answer the current question with something valid and move on (autoplay/tests)."""
        q = self.question
        if isinstance(q, Consent):
            self.values[q.id] = q.agree
            self.next_after_consent()
            return
        if isinstance(q, MultipleChoice):
            first = q.render_options(self.context)[0]
            self.values[q.id] = [first] if q.allow_multiple else first
        elif isinstance(q, Likert):
            self.values[q.id] = (q.scale + 1) // 2
        elif isinstance(q, Slider):
            self.values[q.id] = q.snap(q.start if q.start is not None else q.min)
        elif isinstance(q, TextAnswer):
            self.values[q.id] = "1" if q.numbers_only else "auto"
        self.next()

    def next_after_consent(self) -> None:
        self.index += 1
        if self.index >= len(self.questions):
            self.index = len(self.questions) - 1
            self.done = True

    # --- Layout (shared by drawing and clicking) ---

    def _text_bottom(self) -> int:
        lines = ui.wrap(self.question.render_text(self.context), TEXT_SIZE, WIDTH)
        return 110 + len(lines) * ui.font(TEXT_SIZE).get_linesize() + 30

    def _option_rects(self) -> list[pygame.Rect]:
        q = self.question
        top = self._text_bottom()
        if isinstance(q, MultipleChoice):
            return [
                pygame.Rect(MARGIN, top + i * (OPTION_HEIGHT + 10), WIDTH, OPTION_HEIGHT)
                for i in range(len(q.options))
            ]
        if isinstance(q, Likert):
            gap = 10
            box = min(70, (WIDTH - gap * (q.scale - 1)) // q.scale)
            total = q.scale * box + (q.scale - 1) * gap
            left = MARGIN + (WIDTH - total) // 2
            return [pygame.Rect(left + i * (box + gap), top, box, box) for i in range(q.scale)]
        if isinstance(q, Consent):
            w = 220
            return [
                pygame.Rect(MARGIN + WIDTH // 2 - w - 20, top + 20, w, BUTTON_H + 10),
                pygame.Rect(MARGIN + WIDTH // 2 + 20, top + 20, w, BUTTON_H + 10),
            ]
        return []

    def _slider_track(self) -> pygame.Rect:
        return pygame.Rect(MARGIN + 40, self._text_bottom() + 50, WIDTH - 80, 8)

    def _text_box(self) -> pygame.Rect:
        return pygame.Rect(MARGIN, self._text_bottom(), WIDTH, 50)

    def _back_rect(self) -> pygame.Rect:
        return pygame.Rect(MARGIN, config.SCREEN_HEIGHT - 80, BUTTON_W, BUTTON_H)

    def _next_rect(self) -> pygame.Rect:
        return pygame.Rect(
            config.SCREEN_WIDTH - MARGIN - BUTTON_W, config.SCREEN_HEIGHT - 80, BUTTON_W, BUTTON_H
        )

    # --- Input ---

    def _choose(self, i: int) -> None:
        q = self.question
        if isinstance(q, MultipleChoice) and 0 <= i < len(q.options):
            options = q.render_options(self.context)
            option = options[i]
            if q.allow_multiple:
                chosen = list(self.values.get(q.id) or [])
                chosen.remove(option) if option in chosen else chosen.append(option)
                self.values[q.id] = [o for o in options if o in chosen]
            else:
                self.values[q.id] = option
        elif isinstance(q, Likert) and 0 <= i < q.scale:
            self.values[q.id] = i + 1
        elif isinstance(q, Consent):
            if i == 0:
                self.values[q.id] = q.agree
                self.next_after_consent()
            elif i == 1:
                self.values[q.id] = q.decline
                self.declined = True
                self.done = True

    def _set_slider_from_x(self, x: int) -> None:
        q = self.question
        assert isinstance(q, Slider)
        track = self._slider_track()
        frac = (x - track.left) / track.width
        self.values[q.id] = q.snap(q.min + frac * (q.max - q.min))

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.done:
            return
        q = self.question
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._next_rect().collidepoint(event.pos) and not isinstance(q, Consent):
                self.next()
            elif self._back_rect().collidepoint(event.pos) and self.index > 0:
                self.back()
            elif isinstance(q, Slider):
                track = self._slider_track().inflate(0, 40)
                if track.collidepoint(event.pos):
                    self._dragging = True
                    self._set_slider_from_x(event.pos[0])
            else:
                for i, rect in enumerate(self._option_rects()):
                    if rect.collidepoint(event.pos):
                        self._choose(i)
                        break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging and isinstance(q, Slider):
            self._set_slider_from_x(event.pos[0])
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)

    def _handle_key(self, event: pygame.event.Event) -> None:
        q = self.question
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.next()
        elif isinstance(q, TextAnswer):
            text = str(self.values.get(q.id) or "")
            if event.key == pygame.K_BACKSPACE:
                text = text[:-1]
            elif event.unicode and event.unicode.isprintable() and len(text) < q.max_len:
                if not q.numbers_only or event.unicode.isdigit():
                    text += event.unicode
            self.values[q.id] = text
        elif isinstance(q, Slider) and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            current = self.values.get(q.id)
            if current is None:
                current = q.start if q.start is not None else (q.min + q.max) / 2
            delta = q.step if event.key == pygame.K_RIGHT else -q.step
            self.values[q.id] = q.snap(current + delta)
        elif event.unicode and event.unicode.isdigit() and event.unicode != "0":
            self._choose(int(event.unicode) - 1)

    def update(self, keys: Any = None) -> None:
        """Nothing moves on a survey page; here so every screen has the same methods."""

    # --- Drawing ---

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(config.COLOR_BG)
        if not self.questions:
            return
        q = self.question
        progress = f"{self.title}  ·  {self.index + 1} of {len(self.questions)}"
        ui.draw_text_block(surface, progress, 24, MARGIN, 40, WIDTH, (150, 155, 170))
        ui.draw_text_block(surface, q.render_text(self.context), TEXT_SIZE, MARGIN, 110, WIDTH)
        value = self.values.get(q.id)

        if isinstance(q, MultipleChoice):
            chosen = value if isinstance(value, list) else [value]
            options = q.render_options(self.context)
            for i, (rect, option) in enumerate(zip(self._option_rects(), options, strict=True)):
                ui.draw_button(surface, rect, f"{i + 1}.  {option}", selected=option in chosen)
            if q.allow_multiple:
                hint = "Choose all that apply."
                ui.draw_text_block(
                    surface, hint, 22, MARGIN, rect.bottom + 12, WIDTH, (150, 155, 170)
                )
        elif isinstance(q, Likert):
            rects = self._option_rects()
            for i, rect in enumerate(rects):
                ui.draw_button(surface, rect, str(i + 1), selected=value == i + 1, size=30)
            label_y = rects[0].bottom + 10
            small = (170, 175, 190)
            ui.draw_text_block(surface, q.low_label, 22, rects[0].left - 30, label_y, 140, small)
            right = rects[-1].right - 110
            ui.draw_text_block(surface, q.high_label, 22, right, label_y, 140, small)
            if q.mid_label:
                mid = rects[len(rects) // 2].centerx - 70
                ui.draw_text_block(surface, q.mid_label, 22, mid, label_y, 140, small, center=True)
        elif isinstance(q, Slider):
            track = self._slider_track()
            pygame.draw.rect(surface, (70, 76, 96), track, border_radius=4)
            shown = value if value is not None else (q.start if q.start is not None else q.min)
            frac = (shown - q.min) / (q.max - q.min) if q.max > q.min else 0
            handle = (track.left + round(frac * track.width), track.centery)
            colour = config.COLOR_HUMAN if value is not None else (120, 125, 140)
            pygame.draw.circle(surface, colour, handle, 14)
            label = (
                f"{shown} {q.unit}".strip()
                if value is not None
                else "Drag the slider, or use the left / right arrow keys"
            )
            ui.draw_text_block(surface, label, 30, MARGIN, track.bottom + 25, WIDTH, center=True)
            ends = f"{q.min} {q.unit}".strip(), f"{q.max} {q.unit}".strip()
            ui.draw_text_block(surface, ends[0], 22, track.left - 20, track.top - 30, 100)
            ui.draw_text_block(surface, ends[1], 22, track.right - 60, track.top - 30, 100)
        elif isinstance(q, TextAnswer):
            box = self._text_box()
            pygame.draw.rect(surface, (52, 58, 76), box, border_radius=6)
            pygame.draw.rect(surface, config.COLOR_HUMAN, box, width=2, border_radius=6)
            text = str(value or "")
            cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            surf = ui.font(30).render(text + cursor, True, config.COLOR_TEXT)
            surface.blit(surf, (box.left + 12, box.centery - surf.get_height() // 2))
        elif isinstance(q, Consent):
            agree, decline = self._option_rects()
            ui.draw_button(surface, agree, q.agree)
            ui.draw_button(surface, decline, q.decline)

        if self.index > 0:
            ui.draw_button(surface, self._back_rect(), "Back")
        if not isinstance(q, Consent):
            label = q.button if isinstance(q, Info) else "Next"
            ui.draw_button(surface, self._next_rect(), label, enabled=self.can_continue())
