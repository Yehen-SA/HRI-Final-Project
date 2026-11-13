"""Rules of the basic game, run headless (no window)."""

import pytest

import config
from actions import LEFT, STAY
from engine import HUMAN, ROBOT, score_text
from engine import Game as _Game
from robot_strategies import Strategy


def Game(**kwargs) -> _Game:  # noqa: N802
    """These tests use the predictable sweeping robot unless they say otherwise."""
    kwargs.setdefault("robot_strategy", Strategy.SWEEP)
    return _Game(**kwargs)


def flying(game: Game, ball, x: float, y: float, vx: float, vy: float, hit_by: str) -> None:
    ball.waiting = False
    ball.x, ball.y, ball.vx, ball.vy = x, y, vx, vy
    ball.last_hit_by = hit_by


def park_robot_ball(game: Game) -> None:
    """Keep the robot's ball waiting so it can't interfere with a test."""
    game.robot_ball.launch_tick = 10**9


def test_brick_points_by_row() -> None:
    game = Game()
    points = {b.row: b.points for b in game.bricks}
    assert [points[r] for r in range(config.BRICK_ROWS)] == [7, 7, 4, 4, 1, 1]


@pytest.mark.parametrize("hitter", [HUMAN, ROBOT])
def test_brick_credit_goes_to_last_paddle_hit(hitter: str) -> None:
    game = Game()
    park_robot_ball(game)
    brick = next(b for b in game.bricks if b.row == 0)
    ball = game.human_ball
    flying(game, ball, brick.rect.centerx, brick.rect.bottom + ball.radius + 1, 0, -3, hitter)
    game.update()
    assert not brick.alive
    assert game.scores[hitter] == 7
    assert ball.vy > 0  # bounced off the brick


def test_only_one_brick_per_frame() -> None:
    game = Game()
    park_robot_ball(game)
    a, b = game.bricks[0], game.bricks[1]  # neighbours in the top row
    ball = game.human_ball
    flying(
        game, ball, (a.rect.right + b.rect.left) / 2, a.rect.bottom + ball.radius - 1, 0, -1, HUMAN
    )
    game.update()
    assert game.bricks_left == len(game.bricks) - 1


def test_launch_credits_owner() -> None:
    game = Game()
    game.update(launch_pressed=True)
    assert not game.human_ball.waiting
    assert game.human_ball.last_hit_by == HUMAN
    assert game.human_ball.vy < 0


def test_robot_paddle_can_hit_human_ball_and_takes_credit() -> None:
    game = Game()
    park_robot_ball(game)
    game.human.x = 0  # human far away
    ball = game.human_ball
    flying(game, ball, game.robot.centre_x, game.robot.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()
    assert ball.last_hit_by == ROBOT
    assert ball.vy < 0


def test_double_touch_goes_to_owner() -> None:
    game = Game()
    park_robot_ball(game)
    game.human.x = game.robot.x  # paddles overlap
    ball = game.human_ball
    flying(game, ball, game.robot.centre_x, game.robot.y - ball.radius - 1, 0, 3, ROBOT)
    game.update()
    assert ball.last_hit_by == HUMAN


def test_bounce_angle_depends_on_hit_position() -> None:
    game = Game()
    park_robot_ball(game)
    game.robot.x = 600
    ball = game.human_ball
    centre = game.human.centre_x
    flying(game, ball, centre, game.human.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()
    assert abs(ball.vx) < 0.2  # middle: nearly straight up
    flying(
        game, ball, centre + game.human.width / 2 - 2, game.human.y - ball.radius - 1, 0, 3, HUMAN
    )
    game.update()
    assert ball.vx > 3  # right edge: steep to the right
    assert ball.vx**2 + ball.vy**2 == pytest.approx(config.BALL_SPEED**2)


def test_lost_ball_waits_on_its_paddle_until_space() -> None:
    game = Game()
    park_robot_ball(game)
    ball = game.human_ball
    flying(game, ball, 50, config.SCREEN_HEIGHT + 20, 0, 3, HUMAN)
    game.human.x = 600
    game.update()
    assert ball.waiting
    assert game.drops[HUMAN] == 1
    for _ in range(30):
        game.update(LEFT)
    assert ball.waiting
    assert ball.x == pytest.approx(game.human.centre_x)
    game.update(launch_pressed=True)
    assert not ball.waiting


def test_robot_ball_launches_after_delay() -> None:
    game = Game()
    delay = round(config.ROBOT_RELAUNCH_DELAY_S * config.FPS)
    for _ in range(delay):
        game.update()
    assert game.robot_ball.waiting
    game.update()
    assert not game.robot_ball.waiting


def test_robot_sweeps_full_width() -> None:
    game = Game(robot_strategy=Strategy.SWEEP)
    park_robot_ball(game)
    xs = []
    for _ in range(config.SCREEN_WIDTH):  # long enough for a full crossing both ways
        game.update()
        xs.append(game.robot.x)
    assert min(xs) == 0
    assert max(xs) == config.SCREEN_WIDTH - config.PADDLE_WIDTH


def test_game_ends_on_timer() -> None:
    game = Game(round_seconds=1)
    for _ in range(config.FPS):
        assert not game.over
        game.update()
    assert game.over
    tick = game.tick
    game.update()
    assert game.tick == tick  # nothing moves after game over


def test_game_ends_when_bricks_gone() -> None:
    game = Game()
    for brick in game.bricks:
        brick.alive = False
    game.update()
    assert game.over


def test_same_seed_same_launches() -> None:
    def launch_velocities(seed: int) -> list[tuple[float, float]]:
        game = Game(seed=seed)
        out = []
        for _ in range(3):
            game.human_ball.waiting = True
            game.update(STAY, launch_pressed=True)
            out.append((game.human_ball.vx, game.human_ball.vy))
        return out

    assert launch_velocities(1) == launch_velocities(1)
    assert launch_velocities(1) != launch_velocities(2)


def test_score_text() -> None:
    scores = {HUMAN: 20, ROBOT: 14}
    assert score_text(scores, "shared") == "Team: 34"
    assert score_text(scores, "split") == "You: 20 · Robot: 14 · Total: 34"
    with pytest.raises(ValueError):
        score_text(scores, "other")
