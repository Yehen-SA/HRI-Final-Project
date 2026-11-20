"""Questions after each robot round, and (optionally) at the very end.

- POST_ROUND_QUESTIONS are asked after every round with a robot (so twice, once per robot).
  Items 1-10 match the post-experiment questionnaire in the report's appendix, with "the robot"
  replaced by the robot's name. Two measures the report relies on are added: the Godspeed
  likeability items, and for shared-score participants, the robot's share of the score
  (perceived contribution).
- FINAL_QUESTIONS are asked once at the end. Empty: the appendix has no final questions, so
  the session goes straight to the debrief. Add questions here to bring that stage back.

Question types are explained at the top of questions.py. `show_if=shared_only` limits a
question to one score condition. Every `id` must be unique within its list.
"""

from questions import Context, Info, Likert, Question, Slider, TextAnswer


def shared_only(context: Context) -> bool:
    return context["score_mode"] == "shared"


def split_only(context: Context) -> bool:
    return context["score_mode"] == "split"


def agree(item_id: str, text: str, **kwargs) -> Likert:
    """One statement on the appendix's 5-point agree/disagree scale."""
    return Likert(
        id=item_id,
        text=text,
        scale=5,
        low_label="Strongly disagree",
        mid_label="Neither agree nor disagree",
        high_label="Strongly agree",
        **kwargs,
    )


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
        text=(
            "That round is over. Please say how much you agree or disagree with each statement "
            "about {robot_name}, from 1 (strongly disagree) to 5 (strongly agree)."
        ),
    ),
    # Teammate perception (appendix 1-3)
    agree("part_of_team", "I felt that {robot_name} was part of my team."),
    agree("common_goal", "I felt that {robot_name} and I were working towards a common goal."),
    # With part_of_team (and "competing", split only), places the robot as teammate, competitor
    # or tool.
    agree("felt_like_tool", "I felt that {robot_name} was just a tool."),
    # Robot evaluation (appendix 4-5; liking is covered by the Godspeed items below)
    agree("capable", "I considered {robot_name} capable of performing its role in the game."),
    agree("would_trust", "I would trust {robot_name} to contribute to a team task."),
    # Teamwork experience, shared score (appendix 6-8)
    agree(
        "valuable_contribution",
        "I felt that {robot_name} made a valuable contribution to our team's performance.",
        show_if=shared_only,
    ),
    agree(
        "workload_fair",
        "I felt that the workload was fairly shared between {robot_name} and me.",
        show_if=shared_only,
    ),
    agree(
        "motivated_team_score",
        "I was motivated to improve our team's overall score.",
        show_if=shared_only,
    ),
    # Teamwork experience, separate scores (appendix 6-8)
    agree(
        "own_score_attention",
        "I paid more attention to my own score than to {robot_name}'s score.",
        show_if=split_only,
    ),
    agree("competing", "I felt that I was competing with {robot_name}.", show_if=split_only),
    agree(
        "motivated_own_score",
        "Having separate scores made me more motivated to improve my own performance.",
        show_if=split_only,
    ),
    # Overall teamwork experience (appendix 9)
    agree(
        "willing_to_help",
        "I was willing to help {robot_name} when it was struggling during the game.",
    ),
    # Likeability: Godspeed likeability subscale (report: dependent variables)
    godspeed("like", "Dislike", "Like"),
    godspeed("friendly", "Unfriendly", "Friendly"),
    godspeed("kind", "Unkind", "Kind"),
    godspeed("pleasant", "Unpleasant", "Pleasant"),
    godspeed("nice", "Awful", "Nice"),
    # Perceived contribution, shared score only (report: dependent variables)
    Slider(
        id="robot_share_estimate",
        text="What share of the team's points do you think {robot_name} scored?",
        min=0,
        max=100,
        step=5,
        unit="%",
        start=50,
        show_if=shared_only,
    ),
    # Additional feedback (appendix 10)
    TextAnswer(
        id="feedback",
        text=(
            "Is there anything else you would like to share about your experience playing "
            "with {robot_name}? (optional)"
        ),
        required=False,
    ),
]

FINAL_QUESTIONS: list[Question] = []
