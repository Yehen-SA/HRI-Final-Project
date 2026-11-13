"""Text shown between the stages of a session. Edit freely.

These are lists of questions.Info pages (one page each). `{robot_name}`, `{robot_colour}`,
`{round_number}`,
`{rounds}`, `{practice_seconds}` and `{round_minutes}` are filled in.
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
            "Your paddle is blue. A ball takes the colour of whoever hit it last, and that "
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
        button="Start practice",
    ),
]

ROUND_INTRO = [
    Info(
        id="round_intro",
        text=(
            "Round {round_number} of {rounds}\n\n"
            "You will now play together with a robot teammate called {robot_name}. "
            "{robot_name}'s paddle is {robot_colour}.\n\n"
            "The round lasts {round_minutes} minutes."
        ),
        button="Start round",
    ),
]

ROUND_OVER = "Round over. Press Space to continue."
PRACTICE_OVER = "Practice over. Press Space to continue."

END = "That's the end of the study. Thank you for taking part!\n\nYou can close this window now."
END_SEND_LOG = "Please send this file back to the researchers:\n\n{log_path}"
END_WEB_LOG = (
    "Your browser has downloaded your results file ({log_name}). Please send it back to the "
    "researchers.\n\nIf it didn't download, press D to try again."
)

DECLINED = (
    "Thank you for your time. You chose not to take part, so the study ends here.\n\n"
    "You can close this window now."
)
