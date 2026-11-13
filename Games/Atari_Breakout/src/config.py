"""Game tuning values. Change numbers here; no other file should hard-code them.

Robot behaviour is tuned separately, in robot_strategies.py.
Positions and sizes are in pixels; speeds are in pixels per frame.
"""

# --- Window ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
HUD_HEIGHT = 40  # info bar along the top
WINDOW_TITLE = "HRI Breakout: Human + Robot"

# --- Paddles ---
# Both paddles share one row and can pass through each other.
# PADDLE_Y is the top edge of the row; START_X values are each paddle's left edge.
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 12
PADDLE_SPEED = 7  # human paddle
ROBOT_PADDLE_SPEED = PADDLE_SPEED  # same as the human, so speed isn't a difference between robots
PADDLE_Y = 560
HUMAN_START_X = SCREEN_WIDTH // 4 - PADDLE_WIDTH // 2
ROBOT_START_X = 3 * SCREEN_WIDTH // 4 - PADDLE_WIDTH // 2

# --- Balls ---
# Two balls, one per player, drawn in that player's colour (COLOR_HUMAN / COLOR_ROBOT).
# Each starts just above its owner's paddle.
# A ball waits on its owner's paddle at the start and after it's lost. The human launches
# theirs with Space; the robot's launches by itself after ROBOT_RELAUNCH_DELAY_S.
# Balls pass through each other.
BALL_RADIUS = 7
BALL_SPEED = 5.0  # constant: balls never speed up
LAUNCH_ANGLE_MIN_DEG = 30  # launch angle from vertical, random in this range, either side
LAUNCH_ANGLE_MAX_DEG = 60
MAX_BOUNCE_ANGLE_DEG = 60  # angle from vertical when a ball hits a paddle's very edge
ROBOT_RELAUNCH_DELAY_S = 1.0
# False: a paddle only bounces its own ball; the other player's ball passes through it.
# True: either paddle can bounce either ball, so players can save each other's ball.
# If both paddles touch a ball in the same frame, the owner's paddle counts as the hit.
PADDLES_HIT_ANY_BALL = True

# --- Bricks ---
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_GAP = 4
BRICK_HEIGHT = 20
BRICK_TOP = HUD_HEIGHT + 40  # y of the top brick row
BRICK_WIDTH = (SCREEN_WIDTH - (BRICK_COLS + 1) * BRICK_GAP) // BRICK_COLS
BRICK_ROW_POINTS = [7, 7, 4, 4, 1, 1]  # points per brick, top row first (Atari style)

# --- Rules ---
# A brick's points go to the player whose paddle last hit the ball (the ball's owner if no
# paddle has hit it since launch). No lives: dropping a ball only costs time.
ROUND_SECONDS = 180  # the game ends when time runs out or every brick is gone
SCORE_MODE = "split"  # "shared": team score only; "split": each player's score plus total
SEED = 1234  # seeds the launch angles and the robot, so a run can be repeated

# --- Robot ---
# Strategy for free play: "GOOD", "BAD" or "SWEEP" (see robot_strategies.py), or None for no
# robot. The study session (later) picks the strategy per round itself.
ROBOT_STRATEGY = "GOOD"

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
