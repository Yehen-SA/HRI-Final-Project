"""Robot strategies: how the robot decides where to move.

Pick one with the `Strategy` enum and pass it to `Robot` (robot_agent.py):

    Robot(Strategy.BAD)    # random movement
    Robot(Strategy.GOOD)   # tries to play properly

Each strategy is a class with `act(observation) -> action` and its tuning values at the top.
To add one: write a class with the same two methods, add a name to `Strategy` and an entry to
`STRATEGIES`.

The observation is built by the engine (Game._observation_for_robot):
  - tick, screen_width, screen_height, paddle_y
  - robot_paddle, human_paddle: {"x", "y", "width"} (x is the left edge)
  - balls: list of {"id", "x", "y", "vx", "vy", "radius", "owner", "waiting"}
  - bricks_left
"""

import random
from collections import deque
from enum import Enum
from typing import Any

from actions import LEFT, RIGHT, STAY

Observation = dict[str, Any]


class Strategy(Enum):
    SWEEP = "sweep"  # sweeps the full width, ignoring the balls (testing only)
    BAD = "bad"  # random movement
    GOOD = "good"  # follows the most urgent ball, with human-like delay and error


def _move_towards(paddle_centre: float, target_x: float, deadzone: float) -> str:
    if abs(target_x - paddle_centre) <= deadzone:
        return STAY
    return LEFT if target_x < paddle_centre else RIGHT


class SweepStrategy:
    """Sweeps left and right across the whole screen, turning at each edge."""

    def __init__(self, rng: random.Random) -> None:
        self.direction = RIGHT

    def act(self, obs: Observation) -> str:
        paddle = obs["robot_paddle"]
        if paddle["x"] <= 0:
            self.direction = RIGHT
        elif paddle["x"] + paddle["width"] >= obs["screen_width"]:
            self.direction = LEFT
        return self.direction


class BadStrategy:
    """Random movement: picks LEFT, RIGHT or STAY and holds it for a random time.

    Holding each choice keeps the movement smooth, so it looks like a (bad) player rather than
    jitter. It ignores the balls, so it only catches them by chance.
    """

    MIN_HOLD_FRAMES = 10
    MAX_HOLD_FRAMES = 40
    CHOICES = (LEFT, RIGHT, STAY)
    WEIGHTS = (0.4, 0.4, 0.2)  # chance of each choice

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.action = STAY
        self.frames_left = 0

    def act(self, obs: Observation) -> str:
        paddle = obs["robot_paddle"]
        at_left = paddle["x"] <= 0 and self.action == LEFT
        at_right = paddle["x"] + paddle["width"] >= obs["screen_width"] and self.action == RIGHT
        if self.frames_left <= 0 or at_left or at_right:
            self.action = self.rng.choices(self.CHOICES, self.WEIGHTS)[0]
            self.frames_left = self.rng.randint(self.MIN_HOLD_FRAMES, self.MAX_HOLD_FRAMES)
        self.frames_left -= 1
        return self.action


class GoodStrategy:
    """Tries to play properly, like a reasonable human player.

    Goes for whichever falling ball will reach the paddle row soonest (any colour), aiming at
    where it will land after wall bounces. It reacts to what it saw a few frames ago and aims
    with a small error, and now and then misjudges a ball badly, so it isn't perfect. With no
    ball falling it drifts back towards its home position.
    """

    REACTION_DELAY_FRAMES = 8  # acts on the ball positions from this many frames ago
    AIM_ERROR_PX = 30  # aim offset, drawn at random once per new target ball
    DEADZONE_PX = 6  # don't move if this close to the target
    MISJUDGE_CHANCE = 0.08  # chance per target ball of aiming well off, so it sometimes misses
    MISJUDGE_PX = (70, 110)  # how far off a misjudged aim is
    HOME_X_FRACTION = 0.75  # where it waits with no ball falling (fraction of screen width)

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.history: deque[list[dict[str, Any]]] = deque(maxlen=self.REACTION_DELAY_FRAMES + 1)
        self.target_id: int | None = None
        self.aim_offset = 0.0

    @staticmethod
    def landing_x(ball: dict[str, Any], row_y: float, width: float) -> tuple[float, float]:
        """Frames until a falling ball reaches row_y, and its x there after wall bounces."""
        r = ball["radius"]
        frames = max(0.0, (row_y - r - ball["y"]) / ball["vy"])
        lo, hi = r, width - r
        span = hi - lo
        x = (ball["x"] + ball["vx"] * frames - lo) % (2 * span)
        x = x if x <= span else 2 * span - x
        return frames, lo + x

    def act(self, obs: Observation) -> str:
        self.history.append(obs["balls"])
        seen = self.history[0]  # oldest kept: REACTION_DELAY_FRAMES ago once full
        paddle = obs["robot_paddle"]
        centre = paddle["x"] + paddle["width"] / 2

        falling = [b for b in seen if not b["waiting"] and b["vy"] > 0]
        if not falling:
            self.target_id = None
            home = obs["screen_width"] * self.HOME_X_FRACTION
            return _move_towards(centre, home, self.DEADZONE_PX)

        landings = [
            (*self.landing_x(b, obs["paddle_y"], obs["screen_width"]), b["id"]) for b in falling
        ]
        _, land_x, ball_id = min(landings)
        if ball_id != self.target_id:
            self.target_id = ball_id
            self.aim_offset = self.rng.uniform(-self.AIM_ERROR_PX, self.AIM_ERROR_PX)
            if self.rng.random() < self.MISJUDGE_CHANCE:
                self.aim_offset = self.rng.choice((-1, 1)) * self.rng.uniform(*self.MISJUDGE_PX)
        return _move_towards(centre, land_x + self.aim_offset, self.DEADZONE_PX)


STRATEGIES = {
    Strategy.SWEEP: SweepStrategy,
    Strategy.BAD: BadStrategy,
    Strategy.GOOD: GoodStrategy,
}
