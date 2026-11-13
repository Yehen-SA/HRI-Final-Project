"""Game rules and loop.

`Game` holds the state and rules and never touches the window, so tests can run it headless:
call `update(human_action, launch_pressed)` once per frame. `run()` adds the window, keyboard
and drawing on top.
"""

import asyncio
import math
import random
from typing import Any

import pygame

import config
from actions import STAY
from entities import Ball, Brick, Paddle
from human_controls import LAUNCH_KEY, QUIT_KEY, read_human_action
from robot_agent import Robot
from robot_strategies import Strategy

HUMAN = "human"
ROBOT = "robot"


def score_text(scores: dict[str, int], mode: str) -> str:
    """HUD score line. "shared" shows only the team total; "split" shows both and the total."""
    total = scores[HUMAN] + scores[ROBOT]
    if mode == "shared":
        return f"Team: {total}"
    if mode == "split":
        return f"You: {scores[HUMAN]} · Robot: {scores[ROBOT]} · Total: {total}"
    raise ValueError(f"SCORE_MODE must be 'shared' or 'split', not {mode!r}")


DEFAULT_STRATEGY = Strategy[config.ROBOT_STRATEGY] if config.ROBOT_STRATEGY else None


class Game:
    def __init__(
        self,
        score_mode: str = config.SCORE_MODE,
        seed: int = config.SEED,
        round_seconds: float = config.ROUND_SECONDS,
        robot_strategy: Strategy | None = DEFAULT_STRATEGY,
    ) -> None:
        """`robot_strategy=None` plays without a robot (no robot paddle or ball)."""
        score_text({HUMAN: 0, ROBOT: 0}, score_mode)  # fail early on a bad mode
        self.score_mode = score_mode
        self.rng = random.Random(seed)
        self.round_frames = round(round_seconds * config.FPS)

        self.human = Paddle(
            HUMAN,
            config.HUMAN_START_X,
            config.PADDLE_Y,
            config.PADDLE_WIDTH,
            config.PADDLE_HEIGHT,
            config.PADDLE_SPEED,
            config.SCREEN_WIDTH,
        )
        self.paddles = {HUMAN: self.human}
        self.human_ball = Ball(HUMAN, 0, 0, 0, 0, config.BALL_RADIUS, id=0)
        self.balls = [self.human_ball]

        self.robot_agent: Robot | None = None
        self.robot: Paddle | None = None
        self.robot_ball: Ball | None = None
        if robot_strategy is not None:
            self.robot_agent = Robot(robot_strategy, seed=seed + 1)
            self.robot = Paddle(
                ROBOT,
                config.ROBOT_START_X,
                config.PADDLE_Y,
                config.PADDLE_WIDTH,
                config.PADDLE_HEIGHT,
                config.ROBOT_PADDLE_SPEED,
                config.SCREEN_WIDTH,
            )
            self.paddles[ROBOT] = self.robot
            self.robot_ball = Ball(ROBOT, 0, 0, 0, 0, config.BALL_RADIUS, id=1)
            self.balls.append(self.robot_ball)
        self.bricks = self._build_bricks()

        self.tick = 0
        self.scores = {HUMAN: 0, ROBOT: 0}
        self.drops = {HUMAN: 0, ROBOT: 0}
        self.over = False

        for ball in self.balls:
            self._put_on_paddle(ball)

    # --- Setup ---

    def _build_bricks(self) -> list[Brick]:
        """Lay out the brick grid from the BRICK_* values in config."""
        bricks = []
        for row in range(config.BRICK_ROWS):
            color = config.BRICK_ROW_COLORS[row % len(config.BRICK_ROW_COLORS)]
            points = config.BRICK_ROW_POINTS[row % len(config.BRICK_ROW_POINTS)]
            y = config.BRICK_TOP + row * (config.BRICK_HEIGHT + config.BRICK_GAP)
            for col in range(config.BRICK_COLS):
                x = config.BRICK_GAP + col * (config.BRICK_WIDTH + config.BRICK_GAP)
                rect = pygame.Rect(x, y, config.BRICK_WIDTH, config.BRICK_HEIGHT)
                bricks.append(Brick(rect, color, row, points))
        return bricks

    # --- Helpers ---

    @property
    def bricks_left(self) -> int:
        return sum(b.alive for b in self.bricks)

    @property
    def seconds_left(self) -> int:
        return max(0, math.ceil((self.round_frames - self.tick) / config.FPS))

    def _put_on_paddle(self, ball: Ball) -> None:
        """Make a ball wait on its owner's paddle. The robot's launches after a delay."""
        ball.waiting = True
        ball.vx = ball.vy = 0.0
        ball.launch_tick = self.tick + round(config.ROBOT_RELAUNCH_DELAY_S * config.FPS)
        self._follow_paddle(ball)

    def _follow_paddle(self, ball: Ball) -> None:
        paddle = self.paddles[ball.owner]
        ball.x = paddle.centre_x
        ball.y = paddle.y - ball.radius - 1

    def _launch(self, ball: Ball) -> None:
        """Send a waiting ball upwards at a random angle from vertical, either side."""
        angle = math.radians(
            self.rng.uniform(config.LAUNCH_ANGLE_MIN_DEG, config.LAUNCH_ANGLE_MAX_DEG)
        )
        side = self.rng.choice((-1, 1))
        ball.vx = side * config.BALL_SPEED * math.sin(angle)
        ball.vy = -config.BALL_SPEED * math.cos(angle)
        ball.waiting = False
        ball.last_hit_by = ball.owner

    def _observation_for_robot(self) -> dict[str, Any]:
        """Build the observation passed to Robot.get_action() (keys in robot_strategies.py)."""
        assert self.robot is not None

        def paddle_info(p: Paddle) -> dict[str, Any]:
            return {"x": p.x, "y": p.y, "width": p.width}

        return {
            "tick": self.tick,
            "screen_width": config.SCREEN_WIDTH,
            "screen_height": config.SCREEN_HEIGHT,
            "paddle_y": config.PADDLE_Y,
            "robot_paddle": paddle_info(self.robot),
            "human_paddle": paddle_info(self.human),
            "balls": [
                {
                    "id": b.id,
                    "x": b.x,
                    "y": b.y,
                    "vx": b.vx,
                    "vy": b.vy,
                    "radius": b.radius,
                    "owner": b.owner,
                    "waiting": b.waiting,
                }
                for b in self.balls
            ],
            "bricks_left": self.bricks_left,
        }

    def _apply_action(self, paddle: Paddle, action: str) -> None:
        """Move a paddle. Used for both players; only their speeds differ."""
        paddle.apply(action)

    def _can_bounce(self, paddle: Paddle, ball: Ball) -> bool:
        """Whether this paddle bounces this ball (see config.PADDLES_HIT_ANY_BALL)."""
        return config.PADDLES_HIT_ANY_BALL or paddle.owner == ball.owner

    # --- Ball physics ---

    def _bounce_walls(self, ball: Ball) -> None:
        r = ball.radius
        if ball.x - r < 0:
            ball.x, ball.vx = r, abs(ball.vx)
        elif ball.x + r > config.SCREEN_WIDTH:
            ball.x, ball.vx = config.SCREEN_WIDTH - r, -abs(ball.vx)
        if ball.y - r < config.HUD_HEIGHT:
            ball.y, ball.vy = config.HUD_HEIGHT + r, abs(ball.vy)

    def _hit_brick(self, ball: Ball) -> None:
        """Break at most one brick, credit it, and bounce off it along the shallower overlap."""
        ball_rect = ball.rect
        for brick in self.bricks:
            if not brick.alive or not ball_rect.colliderect(brick.rect):
                continue
            brick.alive = False
            self.scores[ball.last_hit_by] += brick.points
            clip = ball_rect.clip(brick.rect)
            if clip.width < clip.height:
                ball.vx = -abs(ball.vx) if ball.x < brick.rect.centerx else abs(ball.vx)
            else:
                ball.vy = -abs(ball.vy) if ball.y < brick.rect.centery else abs(ball.vy)
            return

    def _hit_paddle(self, ball: Ball) -> None:
        """Bounce off a paddle at an angle set by where it hit. Owner wins a double touch."""
        if ball.vy <= 0:
            return
        touching = [
            p
            for p in self.paddles.values()
            if self._can_bounce(p, ball) and ball.rect.colliderect(p.rect)
        ]
        if not touching:
            return
        paddle = self.paddles[ball.owner] if self.paddles[ball.owner] in touching else touching[0]
        offset = (ball.x - paddle.centre_x) / (paddle.width / 2)
        offset = max(-1.0, min(1.0, offset))
        angle = math.radians(offset * config.MAX_BOUNCE_ANGLE_DEG)
        ball.vx = config.BALL_SPEED * math.sin(angle)
        ball.vy = -config.BALL_SPEED * math.cos(angle)
        ball.y = paddle.y - ball.radius
        ball.last_hit_by = paddle.owner

    def _update_ball(self, ball: Ball, launch_pressed: bool) -> None:
        if ball.waiting:
            self._follow_paddle(ball)
            ready = launch_pressed if ball.owner == HUMAN else self.tick >= ball.launch_tick
            if ready:
                self._launch(ball)
            return
        ball.step()
        self._bounce_walls(ball)
        self._hit_brick(ball)
        self._hit_paddle(ball)
        if ball.y - ball.radius > config.SCREEN_HEIGHT:
            self.drops[ball.owner] += 1
            self._put_on_paddle(ball)

    # --- Frame ---

    def update(self, human_action: str = STAY, launch_pressed: bool = False) -> None:
        """One frame: both paddles, then both balls, then the end check."""
        if self.over:
            return
        self._apply_action(self.human, human_action)
        if self.robot_agent is not None and self.robot is not None:
            self._apply_action(
                self.robot, self.robot_agent.get_action(self._observation_for_robot())
            )
        for ball in self.balls:
            self._update_ball(ball, launch_pressed)
        self.tick += 1
        if self.tick >= self.round_frames or self.bricks_left == 0:
            self.over = True

    # --- Window ---

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the HUD, bricks, both paddles and both balls, each in its owner's colour."""
        screen.fill(config.COLOR_BG)
        pygame.draw.rect(screen, config.COLOR_HUD, (0, 0, config.SCREEN_WIDTH, config.HUD_HEIGHT))
        score = font.render(score_text(self.scores, self.score_mode), True, config.COLOR_TEXT)
        screen.blit(score, (12, (config.HUD_HEIGHT - score.get_height()) // 2))
        mins, secs = divmod(self.seconds_left, 60)
        timer = font.render(f"{mins}:{secs:02d}", True, config.COLOR_TEXT)
        screen.blit(
            timer,
            (
                config.SCREEN_WIDTH - timer.get_width() - 12,
                (config.HUD_HEIGHT - timer.get_height()) // 2,
            ),
        )

        for brick in self.bricks:
            if brick.alive:
                pygame.draw.rect(screen, brick.color, brick.rect)
        colours = {HUMAN: config.COLOR_HUMAN, ROBOT: config.COLOR_ROBOT}
        for paddle in reversed(self.paddles.values()):  # human drawn on top when they overlap
            pygame.draw.rect(screen, colours[paddle.owner], paddle.rect, border_radius=4)
        for ball in self.balls:
            pygame.draw.circle(
                screen, colours[ball.owner], (round(ball.x), round(ball.y)), ball.radius
            )

        if self.human_ball.waiting and not self.over:
            self._centre_text(screen, font, "Press Space to launch your ball", 0.62)
        if self.over:
            shade = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            self._centre_text(screen, font, "Game over", 0.40)
            self._centre_text(screen, font, score_text(self.scores, self.score_mode), 0.48)
            self._centre_text(screen, font, "Space: play again    Esc: quit", 0.58)

    @staticmethod
    def _centre_text(
        screen: pygame.Surface, font: pygame.font.Font, text: str, y_frac: float
    ) -> None:
        surf = font.render(text, True, config.COLOR_TEXT)
        screen.blit(
            surf,
            ((config.SCREEN_WIDTH - surf.get_width()) // 2, round(config.SCREEN_HEIGHT * y_frac)),
        )


async def run(max_frames: int | None = None) -> None:
    """Open the window and play until Esc or the window closes.

    After game over, Space starts a new game. `max_frames` stops early (used by tests).
    The loop is async so the same code can later run in the browser (pygbag).
    """
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.WINDOW_TITLE)
    font = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    game = Game()
    frames = 0
    try:
        while max_frames is None or frames < max_frames:
            space_pressed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == QUIT_KEY:
                        return
                    if event.key == LAUNCH_KEY:
                        space_pressed = True
            if game.over and space_pressed:
                game = Game()
                space_pressed = False
            keys = pygame.key.get_pressed()
            game.update(read_human_action(keys.__getitem__), space_pressed)
            game.draw(screen, font)
            pygame.display.flip()
            clock.tick(config.FPS)
            frames += 1
            await asyncio.sleep(0)
    finally:
        pygame.quit()
