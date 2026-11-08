"""Game tuning values. Change numbers here; no other file should hard-code them.

Robot skill is tuned separately, at the top of robot_agent.py.
Positions and sizes are in pixels; speeds are in pixels per frame.
"""

# --- Window ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
HUD_HEIGHT = 40  # score and lives bar along the top
WINDOW_TITLE = "HRI Breakout: Human + Robot"

# --- Paddles ---
# Both paddles share one row and can pass through each other.
# PADDLE_Y is the top edge of the row; START_X values are each paddle's left edge.
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 12
PADDLE_SPEED = 7
PADDLE_Y = 560
HUMAN_START_X = SCREEN_WIDTH // 4 - PADDLE_WIDTH // 2
ROBOT_START_X = 3 * SCREEN_WIDTH // 4 - PADDLE_WIDTH // 2

# --- Balls ---
# Two balls, one per player, drawn in that player's colour (COLOR_HUMAN / COLOR_ROBOT).
# Each starts just above its owner's paddle.
BALL_RADIUS = 7
BALL_START_SPEED = 5.0
BALL_MAX_SPEED = 9.0
BALL_SPEEDUP_PER_HIT = 0.1  # added to speed on each paddle hit, capped at BALL_MAX_SPEED
# False: a paddle only bounces its own ball; the other player's ball passes through it.
# True: either paddle can bounce either ball, so players can save each other's ball.
PADDLES_HIT_ANY_BALL = False

# --- Bricks ---
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_GAP = 4
BRICK_HEIGHT = 20
BRICK_TOP = HUD_HEIGHT + 40  # y of the top brick row
BRICK_WIDTH = (SCREEN_WIDTH - (BRICK_COLS + 1) * BRICK_GAP) // BRICK_COLS

# --- Rules ---
START_LIVES = 3  # shared by the team; dropping either ball costs one
POINTS_PER_BRICK = 10

# --- Colours (RGB) ---
COLOR_BG = (20, 22, 30)
COLOR_HUD = (30, 34, 46)
COLOR_TEXT = (240, 240, 245)
COLOR_HUMAN = (66, 135, 245)  # human's paddle and ball
COLOR_ROBOT = (245, 180, 66)  # robot's paddle and ball
BRICK_ROW_COLORS = [  # top row first; reused from the top if there are more rows
    (220, 70, 70),
    (230, 130, 60),
    (230, 200, 70),
    (90, 190, 100),
    (70, 150, 220),
    (150, 100, 210),
]
