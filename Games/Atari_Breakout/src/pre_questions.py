"""Stage 1: questions before the game.

Edit freely: add, remove or reorder entries. Question types and options are explained at the
top of questions.py. Every `id` must be unique; it's the column name in the log.

DRAFT wording, based on the report's notes. Check it against the final questionnaire.
"""

from questions import Consent, Info, MultipleChoice, Question, Slider, TextAnswer

PRE_QUESTIONS: list[Question] = [
    Info(
        id="welcome",
        text=(
            "Welcome, and thank you for taking part.\n\n"
            "In this study you will play a short game of Breakout together with a robot "
            "teammate, and answer a few questions before and after each round. "
            "It takes about 15 minutes."
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
    Slider(id="age", text="How old are you?", min=18, max=80, step=1, unit="years", start=25),
    MultipleChoice(
        id="gender",
        text="What is your gender?",
        options=["Female", "Male", "Non-binary", "Other", "Prefer not to say"],
    ),
    MultipleChoice(
        id="played_breakout",
        text="Have you played Atari Breakout (or a similar brick-breaking game) before?",
        options=["Never", "Once or twice", "A few times", "Many times"],
    ),
    MultipleChoice(
        id="gaming_frequency",
        text="How often do you play video games?",
        options=["Never", "Less than once a month", "A few times a month", "Weekly", "Daily"],
    ),
    MultipleChoice(
        id="robot_study_before",
        text="Have you taken part in a study with a robot before?",
        options=["No", "Yes", "Not sure"],
    ),
    TextAnswer(
        id="robot_experience",
        text="Briefly, what experience do you have with robots or AI? (optional)",
        required=False,
    ),
]
