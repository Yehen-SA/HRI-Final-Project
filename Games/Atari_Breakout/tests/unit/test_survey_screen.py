import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from questions import Consent, Info, Likert, MultipleChoice, Slider, TextAnswer
from survey_screen import SurveyScreen

CTX = {"score_mode": "shared", "robot_name": "Robo"}


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


def key(k: int, char: str = "") -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=char)


ENTER = key(pygame.K_RETURN)


def test_required_question_blocks_next_until_answered() -> None:
    s = SurveyScreen("T", [MultipleChoice(id="m", text="?", options=["a", "b"])], CTX)
    s.handle_event(ENTER)
    assert not s.done
    s.handle_event(key(pygame.K_2, "2"))
    s.handle_event(ENTER)
    assert s.done
    assert [(a.question_id, a.answer) for a in s.answers()] == [("m", "b")]


def test_likert_and_info_pages() -> None:
    s = SurveyScreen("T", [Info(id="i", text="hi"), Likert(id="l", text="?", scale=5)], CTX)
    s.handle_event(ENTER)  # Info: always continues
    s.handle_event(key(pygame.K_4, "4"))
    s.handle_event(ENTER)
    assert s.done
    assert [(a.question_id, a.answer) for a in s.answers()] == [("l", 4)]  # Info not logged


def test_multiple_choice_with_several_answers() -> None:
    q = MultipleChoice(id="m", text="?", options=["a", "b", "c"], allow_multiple=True)
    s = SurveyScreen("T", [q], CTX)
    for char in "313":  # c, a, then c again (unticks)
        s.handle_event(key(getattr(pygame, f"K_{char}"), char))
    assert s.values["m"] == ["a"]


def test_slider_must_be_moved_and_uses_arrow_keys() -> None:
    s = SurveyScreen("T", [Slider(id="s", text="?", min=0, max=10, step=1, start=5)], CTX)
    s.handle_event(ENTER)
    assert not s.done
    s.handle_event(key(pygame.K_RIGHT))
    s.handle_event(key(pygame.K_RIGHT))
    s.handle_event(ENTER)
    assert s.done and s.values["s"] == 7


def test_text_answer_typing_backspace_and_numbers_only() -> None:
    s = SurveyScreen(
        "T", [TextAnswer(id="t", text="?"), TextAnswer(id="n", text="?", numbers_only=True)], CTX
    )
    for char in "hix":
        s.handle_event(key(0, char))
    s.handle_event(key(pygame.K_BACKSPACE))
    s.handle_event(ENTER)
    for char in "2a5":
        s.handle_event(key(0, char))
    s.handle_event(ENTER)
    assert s.values == {"t": "hi", "n": "25"}


def test_optional_question_can_be_skipped() -> None:
    s = SurveyScreen("T", [TextAnswer(id="t", text="?", required=False)], CTX)
    s.handle_event(ENTER)
    assert s.done


def test_consent_decline_ends_the_survey() -> None:
    s = SurveyScreen("T", [Consent(id="c", text="?"), Info(id="i", text="later")], CTX)
    s.handle_event(key(pygame.K_2, "2"))
    assert s.done and s.declined
    assert s.values["c"] == "I do not agree"


def test_back_keeps_earlier_answers() -> None:
    qs = [Likert(id="a", text="?"), Likert(id="b", text="?")]
    s = SurveyScreen("T", qs, CTX)
    s.handle_event(key(pygame.K_3, "3"))
    s.handle_event(ENTER)
    s.back()
    assert s.question.id == "a" and s.values["a"] == 3


def test_auto_answer_completes_any_survey_and_drawing_works() -> None:
    from post_questions import POST_ROUND_QUESTIONS
    from pre_questions import PRE_QUESTIONS

    surface = pygame.display.get_surface()
    for questions in (PRE_QUESTIONS, POST_ROUND_QUESTIONS):
        s = SurveyScreen("T", questions, CTX)
        while not s.done:
            s.draw(surface)
            s.auto_answer()
        assert all(
            a.answer not in (None, "") for a in s.answers() if a.question_id != "robot_experience"
        )
