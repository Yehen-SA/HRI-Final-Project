"""Stage 2 and 3: questions after each robot round, and at the very end.

- POST_ROUND_QUESTIONS are asked after every round with the robot (so twice, once per robot).
- FINAL_QUESTIONS are asked once, at the end of the session (stage 3).

Question types are explained at the top of questions.py. `show_if` limits a question to some
participants, e.g. `show_if=shared_only`. Every `id` must be unique within its list.

DRAFT wording, based on the report's notes (teammate perception, CATME-style peer review,
Godspeed likeability, perceived contribution, reward allocation). Check it against the final
questionnaire.
"""

from questions import Context, Info, Likert, MultipleChoice, Question, Slider, TextAnswer


def shared_only(context: Context) -> bool:
    return context["score_mode"] == "shared"


def split_only(context: Context) -> bool:
    return context["score_mode"] == "split"


def godspeed(item_id: str, low: str, high: str) -> Likert:
    """One Godspeed likeability item: a 1-5 scale between two opposite words."""
    return Likert(
        id=f"godspeed_{item_id}",
        text=f"Please rate your impression of {{robot_name}} on this scale: {low} or {high}?",
        scale=5,
        low_label=low,
        high_label=high,
    )


POST_ROUND_QUESTIONS: list[Question] = [
    Info(
        id="post_round_intro",
        text="That round is over. Please answer a few questions about {robot_name} in that round.",
    ),
    MultipleChoice(
        id="robot_role",
        text="In that round, {robot_name} felt most like a...",
        options=["Teammate", "Competitor", "Tool", "None of these"],
    ),
    Likert(
        id="teammate",
        text="I saw {robot_name} as a member of my team.",
        low_label="Strongly disagree",
        high_label="Strongly agree",
    ),
    Likert(
        id="helpful",
        text="{robot_name} contributed to the team's work.",
        low_label="Strongly disagree",
        high_label="Strongly agree",
    ),
    Likert(
        id="reliable",
        text="I could rely on {robot_name} to do its part.",
        low_label="Strongly disagree",
        high_label="Strongly agree",
    ),
    godspeed("like", "Dislike", "Like"),
    godspeed("friendly", "Unfriendly", "Friendly"),
    godspeed("kind", "Unkind", "Kind"),
    godspeed("pleasant", "Unpleasant", "Pleasant"),
    godspeed("nice", "Awful", "Nice"),
    Slider(
        id="robot_share_estimate",
        text="What share of the team's points do you think {robot_name} scored?",
        min=0,
        max=100,
        step=5,
        unit="%",
        start=50,
    ),
    Likert(
        id="robot_vs_me",
        text="How well did {robot_name} do compared to you?",
        low_label="Much worse",
        mid_label="About the same",
        high_label="Much better",
        show_if=shared_only,
    ),
    Likert(
        id="score_competitive",
        text="Seeing {robot_name}'s score made me more competitive.",
        low_label="Strongly disagree",
        high_label="Strongly agree",
        show_if=split_only,
    ),
    Slider(
        id="bonus_to_robot",
        text=(
            "The team has earned 10 bonus points to share between you and {robot_name}. "
            "How many would you give to {robot_name}?"
        ),
        min=0,
        max=10,
        step=1,
        unit="points",
        start=5,
    ),
]

FINAL_QUESTIONS: list[Question] = [
    Info(
        id="final_intro",
        text="Last few questions. These are about the whole session.",
    ),
    MultipleChoice(
        id="preferred_round",
        text="In which round did {robot_name} feel more like a teammate?",
        options=["The first round", "The second round", "No difference"],
    ),
    TextAnswer(
        id="preferred_why",
        text="Why? (optional)",
        required=False,
    ),
    TextAnswer(
        id="comments",
        text="Any other comments about the game or {robot_name}? (optional)",
        required=False,
    ),
]
