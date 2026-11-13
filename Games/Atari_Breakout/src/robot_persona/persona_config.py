"""Robot persona settings. Change the robot's look and voice here."""

import config

NAME = "Robo"  # shown on screen and used in the survey questions

# --- Look ---
# "auto": use PNG images from assets/robot/<expression>.png if there's one for every
# expression, otherwise draw the robot in code. "procedural" or "images" forces one.
SPRITE_SOURCE = "auto"
SPRITE_WIDTH = 84  # px; the head and body are drawn to fit this
SPRITE_HEIGHT = 100
BODY_COLOR = config.COLOR_ROBOT  # matches its paddle
TRIM_COLOR = (200, 140, 40)
FACE_COLOR = (30, 34, 46)  # the screen on its face
EYE_COLOR = (120, 230, 255)
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
PIPER_VOICE = "en_GB-alan-medium"  # Piper voice used by tools/generate_voice.py
PIPER_LENGTH_SCALE = 1.0  # >1 speaks slower

SEED_OFFSET = 3  # persona randomness (which line, blinks) uses config.SEED + this
