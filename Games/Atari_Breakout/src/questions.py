"""Question types for the in-game surveys (pre_questions.py and post_questions.py).

Every question has:
  - id:        short name used in the log and its JSON (keep it unique and stable)
  - text:      what the participant reads. `{robot_name}` and other context keys are filled in.
  - required:  whether they must answer before moving on (default True)
  - show_if:   optional function of the session context; the question is skipped when it
               returns False. Context keys: score_mode ("shared"/"split"), robot (strategy
               name, post-round only), round_number, robot_name, participant_id.

Types:
  Info(id, text)                                    a page of text with a Continue button
  Consent(id, text)                                 "I agree" / "I do not agree"; declining
                                                    ends the session politely
  MultipleChoice(id, text, options=[...])           pick one (or several: allow_multiple=True)
  Likert(id, text, scale=7, low_label, high_label)  a 1..scale rating
  Slider(id, text, min=0, max=100, step=1, unit)    a number on a slider
  TextAnswer(id, text, max_len=200)                 typed answer; numbers_only=True for numbers

Example:
    Likert(id="likeable", text="How likeable was {robot_name}?", scale=5,
           low_label="Not at all", high_label="Very")
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

Context = dict[str, Any]


class _Blank(dict):
    """Leaves unknown {keys} as they are instead of failing."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(kw_only=True)
class Question:
    id: str
    text: str
    required: bool = True
    show_if: Callable[[Context], bool] | None = None

    def visible(self, context: Context) -> bool:
        return self.show_if is None or bool(self.show_if(context))

    def render_text(self, context: Context) -> str:
        return self.text.format_map(_Blank(context))

    def is_answered(self, answer: Any) -> bool:
        return answer not in (None, "", [])

    @property
    def logged(self) -> bool:
        """Whether the answer goes into the log (Info pages don't)."""
        return True


@dataclass(kw_only=True)
class Info(Question):
    required: bool = False
    button: str = "Continue"

    @property
    def logged(self) -> bool:
        return False


@dataclass(kw_only=True)
class Consent(Question):
    agree: str = "I agree"
    decline: str = "I do not agree"


@dataclass(kw_only=True)
class MultipleChoice(Question):
    options: list[str] = field(default_factory=list)
    allow_multiple: bool = False


@dataclass(kw_only=True)
class Likert(Question):
    scale: int = 7
    low_label: str = ""
    high_label: str = ""
    mid_label: str = ""


@dataclass(kw_only=True)
class Slider(Question):
    min: float = 0
    max: float = 100
    step: float = 1
    unit: str = ""
    start: float | None = None  # where the handle starts (default: middle)

    def snap(self, value: float) -> float:
        value = max(self.min, min(self.max, value))
        snapped = self.min + round((value - self.min) / self.step) * self.step
        return int(snapped) if float(self.step).is_integer() else round(snapped, 6)


@dataclass(kw_only=True)
class TextAnswer(Question):
    max_len: int = 200
    numbers_only: bool = False


def visible_questions(questions: list[Question], context: Context) -> list[Question]:
    return [q for q in questions if q.visible(context)]


def check_unique_ids(questions: list[Question]) -> None:
    ids = [q.id for q in questions]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"Duplicate question ids: {sorted(duplicates)}")
