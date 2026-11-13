"""Game rules and loop.

`Game` holds the state and rules and never touches the window, so tests can run it headless:
call `update(human_action, launch_pressed)` once per frame. `run()` adds the window, keyboard
and drawing on top.

Events: everything that happens in a round (brick broken, steal, ball lost...) goes through
`Game._emit()`. Enabled rules from rules.py get a matching `on_<event>` call, and listeners
(logging, robot persona) get `listener(game, event_name, data)`. The event names and their data
are listed in `EVENTS`.
"""

import asyncio
import math
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pygame

import config
import rules as rules_module
from actions import STAY
from entities import Ball, Brick, Paddle, PowerUp
from human_controls import LAUNCH_KEY, QUIT_KEY, read_human_action
from robot_agent import Robot
from robot_strategies import Strategy

HUMAN = "human"
ROBOT = "robot"

# Event name -> the data passed with it. Rules get these as keyword arguments.
EVENTS = {
    "round_start": (),
    "tick": (),
    "ball_launched": ("ball",),
    "paddle_hit": ("paddle", "ball"),
    "steal": ("paddle", "ball", "from_player"),
    "brick_broken": ("ball", "brick"),
    "points": ("player", "points", "reason"),
    "ball_lost": ("ball",),
    "ball_given": ("ball", "player"),
    "powerup_spawned": ("powerup",),
    "powerup_caught": ("paddle", "powerup"),
    "powerup_missed": ("powerup",),
    "round_end": ("reason",),
}

Listener = Callable[["Game", str, dict[str, Any]], None]


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
        lost_ball_to: str = config.LOST_BALL_GOES_TO,
        rules: list[rules_module.Rule] | None = None,
        listeners: list[Listener] | None = None,
    ) -> None:
        """Set up a round.

        - `robot_strategy=None` plays without a robot (no robot paddle or ball).
        - `rules`: the optional rules to use; by default the enabled ones in rules.RULES.
        - `listeners`: called as listener(game, event, data) for every event (see EVENTS).
        """
        if lost_ball_to not in ("random", HUMAN, ROBOT):
            raise ValueError("LOST_BALL_GOES_TO must be 'random', 'human' or 'robot'")
        score_text({HUMAN: 0, ROBOT: 0}, score_mode)  # fail early on a bad mode
        self.score_mode = score_mode
        self.lost_ball_to = lost_ball_to
        self.rng = random.Random(seed)  # launch angles and lost-ball owners
        self.rules_rng = random.Random(
            seed + 2
        )  # for rules, so enabling one doesn't shift the rest
        self.round_frames = round(round_seconds * config.FPS)
        self.rules = rules_module.enabled_rules() if rules is None else list(rules)
        self.listeners = list(listeners or [])

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
        self.balls = [Ball(HUMAN, 0, 0, 0, 0, config.BALL_RADIUS, id=0)]

        self.robot_agent: Robot | None = None
        self.robot: Paddle | None = None
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
            self.balls.append(Ball(ROBOT, 0, 0, 0, 0, config.BALL_RADIUS, id=1))
        self.base_ball_count = len(self.balls)  # extra balls (from rules) vanish when lost
        self._next_ball_id = len(self.balls)
        self.bricks = self._build_bricks()
        self.powerups: list[PowerUp] = []

        self.tick = 0
        self.scores = {HUMAN: 0, ROBOT: 0}
        self.points_by_reason: dict[str, dict[str, int]] = {HUMAN: {}, ROBOT: {}}
        self.drops = {HUMAN: 0, ROBOT: 0}
        self.steals = {HUMAN: 0, ROBOT: 0}  # times each player hit a ball in the other's colour
        self.over = False
        self.end_reason = ""

        for ball in self.balls:
            self._put_on_paddle(ball, ball.owner)
        self._emit("round_start")

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
                bricks.append(Brick(rect, color, row, points, col=col))
        return bricks

    # --- Events ---

    def _emit(self, event: str, **data: Any) -> None:
        """Tell enabled rules (on_<event>) and listeners that something happened."""
        for rule in self.rules:
            getattr(rule, f"on_{event}")(self, **data)
        for listener in self.listeners:
            listener(self, event, data)

    # --- API for rules (see rules.py) ---

    def add_points(self, player: str, points: int, reason: str) -> None:
        """Give (or with a negative number, take) points, recorded under `reason`."""
        self.scores[player] += points
        by_reason = self.points_by_reason[player]
        by_reason[reason] = by_reason.get(reason, 0) + points
        self._emit("points", player=player, points=points, reason=reason)

    def spawn_ball(self, owner: str, x: float, y: float) -> Ball:
        """Add an extra ball in flight, launched upwards from (x, y). It vanishes when lost."""
        ball = Ball(owner, x, y, 0, 0, config.BALL_RADIUS, id=self._next_ball_id)
        self._next_ball_id += 1
        self.balls.append(ball)
        self._launch(ball)
        return ball

    def spawn_powerup(self, kind: str, x: float, y: float) -> PowerUp:
        """Drop a power-up from (x, y). A paddle that catches it triggers on_powerup_caught."""
        size = config.POWERUP_SIZE
        powerup = PowerUp(kind, pygame.Rect(round(x - size / 2), round(y), size, size))
        self.powerups.append(powerup)
        self._emit("powerup_spawned", powerup=powerup)
        return powerup

    # --- Helpers ---

    @property
    def bricks_left(self) -> int:
        return sum(b.alive for b in self.bricks)

    @property
    def seconds_left(self) -> int:
        return max(0, math.ceil((self.round_frames - self.tick) / config.FPS))

    def waiting_balls(self, player: str) -> list[Ball]:
        return [b for b in self.balls if b.waiting and b.owner == player]

    def _put_on_paddle(self, ball: Ball, player: str) -> None:
        """Give a ball to `player`: it waits on their paddle, in their colour.

        The human launches it with Space; the robot's launches by itself after a delay.
        """
        ball.owner = player
        ball.waiting = True
        ball.vx = ball.vy = 0.0
        ball.launch_tick = self.tick + round(config.ROBOT_RELAUNCH_DELAY_S * config.FPS)
        self._follow_paddles()

    def _follow_paddles(self) -> None:
        """Keep waiting balls on their paddle, side by side if there's more than one."""
        for player, paddle in self.paddles.items():
            waiting = self.waiting_balls(player)
            for i, ball in enumerate(waiting):
                spacing = 2 * ball.radius + 4
                ball.x = paddle.centre_x + (i - (len(waiting) - 1) / 2) * spacing
                ball.y = paddle.y - ball.radius - 1

    def _new_owner_for_lost_ball(self) -> str:
        if self.lost_ball_to == "random":
            return self.rng.choice(list(self.paddles))
        return self.lost_ball_to if self.lost_ball_to in self.paddles else HUMAN

    def _launch(self, ball: Ball) -> None:
        """Send a ball upwards at a random angle from vertical, either side."""
        angle = math.radians(
            self.rng.uniform(config.LAUNCH_ANGLE_MIN_DEG, config.LAUNCH_ANGLE_MAX_DEG)
        )
        side = self.rng.choice((-1, 1))
        ball.vx = side * config.BALL_SPEED * math.sin(angle)
        ball.vy = -config.BALL_SPEED * math.cos(angle)
        ball.waiting = False
        self._emit("ball_launched", ball=ball)

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
        """Move a paddle. Used for both players."""
        paddle.apply(action)

    def _can_bounce(self, paddle: Paddle, ball: Ball) -> bool:
        """Whether this paddle bounces this ball (see config.PADDLES_HIT_ANY_BALL)."""
        return config.PADDLES_HIT_ANY_BALL or paddle.owner == ball.owner

    # --- Ball and power-up physics ---

    def _bounce_walls(self, ball: Ball) -> None:
        r = ball.radius
        if ball.x - r < 0:
            ball.x, ball.vx = r, abs(ball.vx)
        elif ball.x + r > config.SCREEN_WIDTH:
            ball.x, ball.vx = config.SCREEN_WIDTH - r, -abs(ball.vx)
        if ball.y - r < config.HUD_HEIGHT:
            ball.y, ball.vy = config.HUD_HEIGHT + r, abs(ball.vy)

    def _hit_brick(self, ball: Ball) -> None:
        """Break at most one brick, credit the ball's owner, and bounce off the brick."""
        ball_rect = ball.rect
        for brick in self.bricks:
            if not brick.alive or not ball_rect.colliderect(brick.rect):
                continue
            brick.alive = False
            clip = ball_rect.clip(brick.rect)
            if clip.width < clip.height:
                ball.vx = -abs(ball.vx) if ball.x < brick.rect.centerx else abs(ball.vx)
            else:
                ball.vy = -abs(ball.vy) if ball.y < brick.rect.centery else abs(ball.vy)
            self.add_points(ball.owner, brick.points, "bricks")
            self._emit("brick_broken", ball=ball, brick=brick)
            return

    def _hit_paddle(self, ball: Ball) -> None:
        """Bounce off a paddle at an angle set by where it hit, and take ownership.

        Hitting a ball in the other player's colour is a steal. If both paddles touch the ball
        in the same frame, its current owner's paddle counts.
        """
        if ball.vy <= 0:
            return
        touching = [
            p
            for p in self.paddles.values()
            if self._can_bounce(p, ball) and ball.rect.colliderect(p.rect)
        ]
        if not touching:
            return
        own = self.paddles.get(ball.owner)
        paddle = own if own in touching else touching[0]
        offset = (ball.x - paddle.centre_x) / (paddle.width / 2)
        offset = max(-1.0, min(1.0, offset))
        angle = math.radians(offset * config.MAX_BOUNCE_ANGLE_DEG)
        ball.vx = config.BALL_SPEED * math.sin(angle)
        ball.vy = -config.BALL_SPEED * math.cos(angle)
        ball.y = paddle.y - ball.radius
        if paddle.owner != ball.owner:
            from_player = ball.owner
            self.steals[paddle.owner] += 1
            ball.owner = paddle.owner
            self._emit("steal", paddle=paddle, ball=ball, from_player=from_player)
        self._emit("paddle_hit", paddle=paddle, ball=ball)

    def _lose_ball(self, ball: Ball) -> None:
        """Count a drop, then give the ball to a player (or remove it if it was an extra)."""
        self.drops[ball.owner] += 1
        self._emit("ball_lost", ball=ball)
        if len(self.balls) > self.base_ball_count:
            self.balls.remove(ball)
            return
        player = self._new_owner_for_lost_ball()
        self._put_on_paddle(ball, player)
        self._emit("ball_given", ball=ball, player=player)

    def _update_ball(self, ball: Ball) -> None:
        if ball.waiting:
            if ball.owner == ROBOT and self.tick >= ball.launch_tick:
                self._launch(ball)
            return
        ball.step()
        self._bounce_walls(ball)
        self._hit_brick(ball)
        self._hit_paddle(ball)
        if ball.y - ball.radius > config.SCREEN_HEIGHT:
            self._lose_ball(ball)

    def _update_powerup(self, powerup: PowerUp) -> None:
        powerup.rect.y += config.POWERUP_FALL_SPEED
        for paddle in self.paddles.values():
            if powerup.rect.colliderect(paddle.rect):
                self.powerups.remove(powerup)
                self._emit("powerup_caught", paddle=paddle, powerup=powerup)
                return
        if powerup.rect.top > config.SCREEN_HEIGHT:
            self.powerups.remove(powerup)
            self._emit("powerup_missed", powerup=powerup)

    # --- Frame ---

    def update(self, human_action: str = STAY, launch_pressed: bool = False) -> None:
        """One frame: both paddles, then the balls and power-ups, then the end check.

        `launch_pressed` (Space this frame) launches one of the human's waiting balls.
        """
        if self.over:
            return
        self._apply_action(self.human, human_action)
        if self.robot_agent is not None and self.robot is not None:
            self._apply_action(
                self.robot, self.robot_agent.get_action(self._observation_for_robot())
            )
        self._follow_paddles()
        if launch_pressed and (waiting := self.waiting_balls(HUMAN)):
            self._launch(waiting[0])
        for ball in list(self.balls):  # copy: rules may add balls, lost extras are removed
            self._update_ball(ball)
        for powerup in list(self.powerups):
            self._update_powerup(powerup)
        self._emit("tick")
        self.tick += 1
        if self.tick >= self.round_frames:
            self.end("timer")
        elif self.bricks_left == 0:
            self.end("bricks_cleared")

    def end(self, reason: str) -> None:
        """Finish the round: "timer", "bricks_cleared", or "quit" (from the session)."""
        if self.over:
            return
        self.over = True
        self.end_reason = reason
        self._emit("round_end", reason=reason)

    # --- Window ---

    def hud_score_text(self) -> str:
        """The score line: per score mode, or just the human's score with no robot."""
        if self.robot is None:
            return f"Score: {self.scores[HUMAN]}"
        return score_text(self.scores, self.score_mode)

    def draw(
        self, screen: pygame.Surface, font: pygame.font.Font, end_overlay: bool = True
    ) -> None:
        """Draw the HUD, bricks, paddles, power-ups and balls (each in its owner's colour).

        `end_overlay=False` leaves out the free-play "Game over / play again" overlay.
        """
        screen.fill(config.COLOR_BG)
        pygame.draw.rect(screen, config.COLOR_HUD, (0, 0, config.SCREEN_WIDTH, config.HUD_HEIGHT))
        score = font.render(self.hud_score_text(), True, config.COLOR_TEXT)
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
        for powerup in self.powerups:
            pygame.draw.rect(screen, config.COLOR_POWERUP, powerup.rect, border_radius=4)
            label = font.render(powerup.kind[:1].upper(), True, config.COLOR_BG)
            screen.blit(label, label.get_rect(center=powerup.rect.center))
        for ball in self.balls:
            pygame.draw.circle(
                screen, colours[ball.owner], (round(ball.x), round(ball.y)), ball.radius
            )

        if self.waiting_balls(HUMAN) and not self.over:
            self._centre_text(screen, font, "Press Space to launch your ball", 0.62)
        if self.over and end_overlay:
            shade = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            self._centre_text(screen, font, "Game over", 0.40)
            self._centre_text(screen, font, self.hud_score_text(), 0.48)
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


async def run(max_frames: int | None = None, log_dir: Path | None = None) -> None:
    """Free play: open the window and play until Esc or the window closes.

    After game over, Space starts a new game. Every game is written to a session log.
    `max_frames` stops early (used by tests). The loop is async so the same code can run in
    the browser (pygbag).
    """
    from session_log import SessionLog  # imported here: session_log imports this module
    from stats import RoundStats

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.WINDOW_TITLE)
    font = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()

    log = SessionLog.create("freeplay", log_dir)
    log.write_participant(
        {"mode": "free play", "score_mode": config.SCORE_MODE, "robot": config.ROBOT_STRATEGY}
    )
    log.write_settings()
    games_played = 0

    def new_game() -> tuple[Game, RoundStats]:
        stats = RoundStats()
        return Game(listeners=[stats]), stats

    def save(game: Game, stats: RoundStats) -> None:
        nonlocal games_played
        games_played += 1
        info = {"title": f"Game {games_played}", "robot": config.ROBOT_STRATEGY}
        log.write_round(info | {"score_mode": game.score_mode}, stats)

    game, stats = new_game()
    saved = False
    frames = 0
    status = "aborted"
    try:
        while max_frames is None or frames < max_frames:
            space_pressed = False
            quit_now = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_now = True
                if event.type == pygame.KEYDOWN:
                    if event.key == QUIT_KEY:
                        quit_now = True
                    if event.key == LAUNCH_KEY:
                        space_pressed = True
            if quit_now:
                break
            if game.over and space_pressed:
                game, stats = new_game()
                saved = False
                space_pressed = False
            keys = pygame.key.get_pressed()
            game.update(read_human_action(keys.__getitem__), space_pressed)
            if game.over and not saved:
                save(game, stats)
                saved = True
            game.draw(screen, font)
            pygame.display.flip()
            clock.tick(config.FPS)
            frames += 1
            await asyncio.sleep(0)
        if not saved:
            game.end("quit")
            save(game, stats)
        status = "complete"
    finally:
        log.finish(status)
        pygame.quit()
