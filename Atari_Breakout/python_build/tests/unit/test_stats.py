import config
from engine import HUMAN, ROBOT, Game
from entities import Ball
from robot_strategies import Strategy
from stats import ROWS, RoundStats


def setup(**kwargs) -> tuple[Game, RoundStats]:
    stats = RoundStats()
    kwargs.setdefault("robot_strategy", Strategy.SWEEP)
    game = Game(rules=[], listeners=[stats], **kwargs)
    next(b for b in game.balls if b.id == 1).launch_tick = 10**9  # park the robot's ball
    return game, stats


def flying(ball: Ball, x: float, y: float, vx: float, vy: float, owner: str) -> None:
    ball.waiting = False
    ball.x, ball.y, ball.vx, ball.vy = x, y, vx, vy
    ball.owner = owner


def test_counts_steals_hits_bricks_and_drops() -> None:
    game, stats = setup(lost_ball_to=HUMAN)
    ball = game.balls[0]
    game.human.x = 0
    flying(ball, game.robot.centre_x, game.robot.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()  # robot steals the human's ball
    brick = game.bricks[0]
    flying(ball, brick.rect.centerx, brick.rect.bottom + ball.radius + 1, 0, -3, ROBOT)
    game.update()  # robot's ball breaks a brick
    flying(ball, 50, config.SCREEN_HEIGHT + 20, 0, 3, ROBOT)
    game.update()  # robot loses it; it goes to the human
    game.end("quit")
    s = stats.summary()
    robot, human = s["players"][ROBOT], s["players"][HUMAN]
    assert robot["steals_made"] == 1 and human["balls_stolen"] == 1
    assert robot["paddle_hits"] == 1 and robot["own_ball_hits"] == 0
    assert robot["bricks_broken"] == 1 and robot["points_bricks"] == 7
    assert robot["balls_lost"] == 1 and human["balls_received"] == 1
    assert s["end_reason"] == "quit"
    assert s["robot_share_of_score"] == 1.0
    events = [e["event"] for e in stats.timeline]
    assert events == ["steal", "paddle_hit", "brick_broken", "ball_lost", "ball_given", "round_end"]


def test_possession_and_waiting_time() -> None:
    game, stats = setup()
    for _ in range(60):  # 1 s: both balls waiting
        game.update()
    game.update(launch_pressed=True)
    for _ in range(59):  # human's ball flies for 1 s in total
        game.update()
    s = stats.summary()["players"]
    assert s[HUMAN]["waiting_s"] == 1.0
    assert s[HUMAN]["possession_s"] == 1.0
    assert s[ROBOT]["waiting_s"] == 2.0


def test_human_launch_delay() -> None:
    game, stats = setup()
    for _ in range(90):
        game.update()
    game.update(launch_pressed=True)
    assert stats.summary()["players"][HUMAN]["launch_delay_mean_s"] == 1.5


def test_paddle_movement_and_overlap() -> None:
    game, stats = setup()
    game.human.x = game.robot.x
    stats._last_x[HUMAN] = game.human.x
    game.update("LEFT")
    s = stats.summary()
    assert s["players"][HUMAN]["paddle_distance_px"] == config.PADDLE_SPEED
    assert s["players"][HUMAN]["moving_s"] > 0
    assert s["paddles_overlapping_s"] > 0


def test_every_row_is_in_the_summary() -> None:
    game, stats = setup()
    game.update()
    players = stats.summary()["players"]
    for key, _ in ROWS:
        assert key in players[HUMAN] and key in players[ROBOT]
