import pytest

import session_text
from post_questions import FINAL_QUESTIONS, POST_ROUND_QUESTIONS
from pre_questions import PRE_QUESTIONS
from questions import (
    Info,
    Likert,
    MultipleChoice,
    Question,
    Slider,
    check_unique_ids,
    visible_questions,
)

ALL_LISTS = {
    "pre": PRE_QUESTIONS,
    "post_round": POST_ROUND_QUESTIONS,
    "final": FINAL_QUESTIONS,
    "instructions": session_text.INSTRUCTIONS,
    "round_intro": session_text.ROUND_INTRO,
}


@pytest.mark.parametrize("name", ALL_LISTS)
def test_question_lists_are_valid(name: str) -> None:
    questions = ALL_LISTS[name]
    check_unique_ids(questions)
    for q in questions:
        assert isinstance(q, Question) and q.id and q.text
        if isinstance(q, MultipleChoice):
            assert len(q.options) >= 2
        if isinstance(q, Likert):
            assert q.scale >= 2
        if isinstance(q, Slider):
            assert q.max > q.min and q.step > 0


def test_duplicate_ids_are_caught() -> None:
    with pytest.raises(ValueError):
        check_unique_ids([Info(id="a", text="x"), Info(id="a", text="y")])


def test_show_if_splits_questions_by_score_mode() -> None:
    shared = {q.id for q in visible_questions(POST_ROUND_QUESTIONS, {"score_mode": "shared"})}
    split = {q.id for q in visible_questions(POST_ROUND_QUESTIONS, {"score_mode": "split"})}
    assert "robot_vs_me" in shared and "robot_vs_me" not in split
    assert "score_competitive" in split and "score_competitive" not in shared


def test_text_fills_in_context_and_leaves_unknown_keys() -> None:
    q = Info(id="x", text="Hi {robot_name}, {unknown}")
    assert q.render_text({"robot_name": "Robo"}) == "Hi Robo, {unknown}"


def test_slider_snaps_to_steps_and_range() -> None:
    s = Slider(id="s", text="?", min=0, max=10, step=1)
    assert s.snap(3.4) == 3 and s.snap(-5) == 0 and s.snap(99) == 10
    assert isinstance(s.snap(3.4), int)
    assert Slider(id="t", text="?", min=0, max=1, step=0.25).snap(0.6) == 0.5


def test_options_fill_in_robot_names() -> None:
    q = MultipleChoice(id="m", text="?", options=["{robot_1_name}", "{robot_2_name}", "Neither"])
    ctx = {"robot_1_name": "Nova", "robot_2_name": "Pip"}
    assert q.render_options(ctx) == ["Nova", "Pip", "Neither"]
