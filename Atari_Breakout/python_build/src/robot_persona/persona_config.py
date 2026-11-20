"""Robot persona settings. Change the robots' names, looks and voice here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    """Who a robot is: its name and colour. Its paddle, balls and body all use the colour."""

    name: str
    colour_name: str  # used in on-screen text, e.g. "Nova's paddle is orange"
    body: tuple[int, int, int]  # paddle, balls and head
    trim: tuple[int, int, int]  # arms, body, antenna (a darker shade)


# The robots, by round: round 1's robot is the first, round 2's the second. Robot order is
# counterbalanced (assignment.py), so each identity is the BAD robot for half the participants
# and the GOOD robot for the other half: name and colour aren't tied to skill.
# Only the name and colour differ; voice, expressions and lines are the same for both.
# The player is cyan (config.COLOR_HUMAN). Yellow and purple differ from cyan in brightness as
# well as hue, so they stay apart even with red-green colour blindness; that matters because a
# ball's colour shows who scores it.
IDENTITIES = [
    Identity("Nova", "yellow", body=(240, 215, 50), trim=(185, 160, 20)),
    Identity("Pip", "purple", body=(170, 110, 215), trim=(120, 72, 165)),
]
FREE_PLAY_IDENTITY = IDENTITIES[0]


def identity_for_round(round_number: int) -> Identity:
    """Round 1 -> IDENTITIES[0], round 2 -> IDENTITIES[1], and so on (wrapping round)."""
    return IDENTITIES[(round_number - 1) % len(IDENTITIES)]


# --- Look ---
# "auto": use PNG images if there's one for every expression, otherwise draw the robot in code.
# Images go in assets/robot/<name>/<expression>.png (e.g. assets/robot/nova/happy.png), or
# assets/robot/<expression>.png to share one set. "procedural" or "images" forces one.
SPRITE_SOURCE = "auto"
SPRITE_WIDTH = 84  # px; the head and body are drawn to fit this
SPRITE_HEIGHT = 100
FACE_COLOR = (30, 34, 46)  # the screen on its face
EYE_COLOR = (240, 244, 252)  # white: kept apart from the player's cyan
BLINK_EVERY_S = (2.5, 5.0)  # random gap between blinks
EXPRESSION_SECONDS = 1.6  # how long a reaction (happy, sad...) shows before going back

# --- Speech ---
SPEECH_ENABLED = True
BUBBLE_SECONDS = 2.6  # how long a speech bubble stays
SPEECH_COOLDOWN_S = 4.0  # minimum gap between lines (higher-priority lines may interrupt)
IDLE_LINE_AFTER_S = 25.0  # say something if it's been quiet this long
BUBBLE_TEXT_SIZE = 24
BUBBLE_MAX_WIDTH = 230

# --- Voice ---
VOICE_ENABLED = True  # play assets/robot/voice/<file>.ogg for each line, if it exists
VOICE_VOLUME = 0.8
PIPER_VOICE = (
    "en_GB-jenny_dioco-medium"  # Piper voice used by tools/generate_voice.py (female, British)
)
PIPER_LENGTH_SCALE = 1.0  # >1 speaks slower

SEED_OFFSET = 3  # persona randomness (which line, blinks) uses config.SEED + this
