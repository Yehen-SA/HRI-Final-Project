"""Stage 1: questions before the game.

Matches the pre-experiment questionnaire in the report's appendix. Edit freely: add, remove or
reorder entries. Question types are explained at the top of questions.py. Every `id` must be
unique; it's the column name in the log.
"""

from questions import Consent, Info, MultipleChoice, Question, TextAnswer

PRE_QUESTIONS: list[Question] = [
    Info(
        id="welcome",
        text=(
            "Welcome, and thank you for taking part.\n\n"
            # Cover story (the report's confounds section): the stated purpose doesn't reveal
            # the hypothesis. The real aim is explained in the debrief at the end.
            "In this study we are looking at how people learn to play a new two-player version "
            "of a classic arcade game alongside a computer-controlled player. You will answer a "
            "few questions, play a short practice round, then two rounds with a robot partner, "
            "with a few questions after each. It takes about 10 minutes."
        ),
    ),
    Consent(
        id="consent",
        text=(
            "Your answers and game data are recorded anonymously under your participant ID "
            "and used only for this university project. You can stop at any time by pressing "
            "Esc twice, and your data will not be used if you ask.\n\n"
            "Do you agree to take part?"
        ),
    ),
    TextAnswer(id="age", text="What is your age?", max_len=3, numbers_only=True),
    MultipleChoice(
        id="gender",
        text="What is your gender?",
        options=["Male", "Female", "Other", "Prefer not to say"],
    ),
    MultipleChoice(
        id="interacted_with_robot",
        text="Have you ever interacted with a robot before?",
        options=["Yes", "No"],
    ),
    MultipleChoice(
        id="played_breakout",
        text="Have you ever played Atari Breakout (the brick-breaking game)?",
        options=["Yes", "No"],
    ),
]
