"""Text shown between the stages of a session. Edit freely.

Info pages are lists of questions.Info (one page each). `{robot_name}`, `{robot_colour}`,
`{round_number}`, `{rounds}`, `{practice_seconds}` and `{round_minutes}` are filled in.
"""

from questions import Info, TextAnswer

PARTICIPANT_ID = TextAnswer(
    id="participant_id",
    text="Please type the participant ID you were given (for example P07), then press Enter.",
    max_len=20,
)

INSTRUCTIONS = [
    Info(
        id="how_to_play",
        text=(
            "How to play\n\n"
            "Move your paddle with A / D or the left / right arrow keys. "
            "Press Space to launch a ball that is waiting on your paddle.\n\n"
            "Break bricks to score points: higher rows are worth more."
        ),
    ),
    Info(
        id="ball_colours",
        text=(
            "Ball colours\n\n"
            "Your paddle is cyan. A ball takes the colour of whoever hit it last, and that "
            "player scores the bricks it breaks. Any paddle can hit any ball.\n\n"
            "When a ball falls off the bottom, it comes back on a random player's paddle."
        ),
    ),
    Info(
        id="practice_intro",
        text=(
            "First, a practice round on your own to get used to the controls. "
            "It lasts {practice_seconds} seconds and is not part of the results."
        ),
        button="Continue",
    ),
]

# Shown on each round's start screen (the robot introduces itself there too). Play and the
# timer start when the participant presses Space to launch their first ball.
PRACTICE_START = "Practice round: {practice_seconds} seconds, on your own\n\nPress Space to start"
ROUND_START = (
    "Round {round_number} of {rounds}: {round_minutes} minutes with {robot_name}\n\n"
    "Press Space to start"
)

ROUND_OVER = "Round over. Press Space to continue."
PRACTICE_OVER = "Practice over. Press Space to continue."

# Debrief: explains the real aim, since the welcome page gives a cover story.
END = (
    "That's the end of the study. Thank you for taking part!\n\n"
    "About this study: we told you it was about learning a new version of an arcade game. "
    "We are actually studying whether showing a shared team score, rather than separate "
    "scores, makes people see a robot partner as a teammate, and whether how well the robot "
    "plays changes this. The two robots were controlled by programs of different skill. "
    "If you'd rather we didn't use your data now that you know this, tell the researchers.\n\n"
    "You can close this window now."
)
END_SEND_LOG = "Please send this file back to the researchers:\n\n{log_path}"
END_WEB_LOG = (
    "Your browser has downloaded your results file ({log_name}). Please send it back to the "
    "researchers.\n\nIf it didn't download, press D to try again."
)

DECLINED = (
    "Thank you for your time. You chose not to take part, so the study ends here.\n\n"
    "You can close this window now."
)
