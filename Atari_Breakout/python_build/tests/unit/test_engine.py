"""Rules of the game, run headless (no window)."""

import pytest

import config
from actions import LEFT, STAY
from engine import HUMAN, ROBOT, score_text
from engine import Game as _Game
from entities import Ball
from robot_strategies import Strategy


def Game(**kwargs) -> _Game:  # noqa: N802
    """These tests use the predictable sweeping robot unless they say otherwise."""
    kwargs.setdefault("robot_strategy", Strategy.SWEEP)
    return _Game(**kwargs)


def ball_of(game: _Game, ball_id: int) -> Ball:
    return next(b for b in game.balls if b.id == ball_id)


def flying(ball: Ball, x: float, y: float, vx: float, vy: float, owner: str) -> None:
    ball.waiting = False
    ball.x, ball.y, ball.vx, ball.vy = x, y, vx, vy
    ball.owner = owner


def park_robot_ball(game: _Game) -> None:
    """Keep the robot's starting ball waiting so it can't interfere with a test."""
    ball_of(game, 1).launch_tick = 10**9


def test_each_player_starts_with_one_ball_in_their_colour() -> None:
    game = Game()
    assert sorted(b.owner for b in game.balls) == [HUMAN, ROBOT]
    assert all(b.waiting for b in game.balls)


def test_brick_points_by_row() -> None:
    game = Game()
    points = {b.row: b.points for b in game.bricks}
    assert [points[r] for r in range(config.BRICK_ROWS)] == [7, 7, 5, 5, 4, 4, 3, 3, 1, 1]


@pytest.mark.parametrize("owner", [HUMAN, ROBOT])
def test_brick_points_go_to_the_balls_owner(owner: str) -> None:
    game = Game()
    park_robot_ball(game)
    brick = next(b for b in game.bricks if b.row == 0)
    ball = ball_of(game, 0)
    flying(ball, brick.rect.centerx, brick.rect.bottom + ball.radius + 1, 0, -3, owner)
    game.update()
    assert not brick.alive
    assert game.scores[owner] == 7
    assert ball.vy > 0  # bounced off the brick


def test_only_one_brick_per_frame() -> None:
    game = Game()
    park_robot_ball(game)
    a, b = game.bricks[0], game.bricks[1]  # neighbours in the top row
    ball = ball_of(game, 0)
    flying(ball, (a.rect.right + b.rect.left) / 2, a.rect.bottom + ball.radius - 1, 0, -1, HUMAN)
    game.update()
    assert game.bricks_left == len(game.bricks) - 1


def test_space_launches_a_human_ball() -> None:
    game = Game()
    game.update(launch_pressed=True)
    ball = ball_of(game, 0)
    assert not ball.waiting
    assert ball.owner == HUMAN
    assert ball.vy < 0


def at_robot_paddle(game: _Game, ball: Ball, owner: str) -> None:
    """Put a ball just above the robot's paddle, falling, in `owner`'s colour."""
    flying(ball, game.robot.centre_x, game.robot.y - ball.radius - 1, 0, 3, owner)


def test_overlapping_paddles_mean_a_steal_by_the_other_player() -> None:
    for owner, taker in ((HUMAN, ROBOT), (ROBOT, HUMAN)):
        game = Game()
        park_robot_ball(game)
        game.human.x = game.robot.x  # paddles overlap: the owner was there too
        ball = ball_of(game, 0)
        at_robot_paddle(game, ball, owner)
        game.update()
        assert ball.owner == taker
        assert game.steals[taker] == 1 and game.rescues == {HUMAN: 0, ROBOT: 0}
        assert ball.vy < 0


def test_taking_a_ball_its_owner_could_not_reach_is_a_rescue() -> None:
    game = Game()
    park_robot_ball(game)
    game.human.x = 0  # human far away
    ball = ball_of(game, 0)
    at_robot_paddle(game, ball, HUMAN)
    game.update()
    assert ball.owner == ROBOT
    assert game.rescues == {HUMAN: 0, ROBOT: 1}
    assert game.steals == {HUMAN: 0, ROBOT: 0}
    assert game.prompted_rescues == {HUMAN: 0, ROBOT: 0}


def test_hitting_your_own_ball_is_neither() -> None:
    game = Game()
    park_robot_ball(game)
    game.robot.x = 600
    ball = ball_of(game, 0)
    flying(ball, game.human.centre_x, game.human.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()
    assert ball.owner == HUMAN
    assert game.steals == {HUMAN: 0, ROBOT: 0} and game.rescues == {HUMAN: 0, ROBOT: 0}


def test_help_requests_are_spread_over_the_round() -> None:
    game = Game(round_seconds=120, help_requests=2)
    assert game.help_request_ticks == [40 * config.FPS, 80 * config.FPS]
    assert Game(help_requests=0).help_request_ticks == []


def test_help_request_marks_a_falling_robot_ball_and_the_robot_cannot_hit_it() -> None:
    events = []
    game = Game(
        round_seconds=10, help_requests=1, rules=[], listeners=[lambda g, e, d: events.append(e)]
    )
    park_robot_ball(game)
    ball = ball_of(game, 1)
    game.tick = game.help_request_ticks[0]
    flying(ball, game.robot.centre_x, 300, 0, 3, ROBOT)
    game.update()
    assert ball.help_requested and "help_request" in events
    assert game.help_requests_made == 1
    game.human.x = 0
    at_robot_paddle(game, ball, ROBOT)  # straight onto the robot's paddle: it doesn't bounce
    game.update()
    assert ball.vy > 0 and ball.owner == ROBOT


def test_rescuing_a_help_requested_ball_is_a_prompted_rescue() -> None:
    game = Game(help_requests=1)
    park_robot_ball(game)
    ball = ball_of(game, 1)
    ball.help_requested = True
    game.human.x = game.robot.x  # even right next to the robot, it's the human's to save
    at_robot_paddle(game, ball, ROBOT)
    game.update()
    assert ball.owner == HUMAN and not ball.help_requested
    assert game.rescues[HUMAN] == 1 and game.prompted_rescues[HUMAN] == 1
    assert game.steals[HUMAN] == 0


def test_robot_moves_away_from_a_ball_it_asked_for_help_with() -> None:
    from robot_agent import Robot

    obs = {
        "screen_width": config.SCREEN_WIDTH,
        "paddle_y": config.PADDLE_Y,
        "robot_paddle": {"x": 350, "y": config.PADDLE_Y, "width": config.PADDLE_WIDTH},
        "human_paddle": {"x": 0, "y": config.PADDLE_Y, "width": config.PADDLE_WIDTH},
        "balls": [
            {
                "id": 1,
                "x": 420,
                "y": 300,
                "vx": 0,
                "vy": 4,
                "radius": 7,
                "owner": ROBOT,
                "waiting": False,
                "help_requested": True,
            }
        ],
    }
    for strategy in (Strategy.GOOD, Strategy.BAD):
        assert Robot(strategy).get_action(obs) == "LEFT"  # lands right of centre: go left


def test_bounce_angle_depends_on_hit_position() -> None:
    game = Game()
    park_robot_ball(game)
    game.robot.x = 600
    ball = ball_of(game, 0)
    centre = game.human.centre_x
    flying(ball, centre, game.human.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()
    assert abs(ball.vx) < 0.2  # middle: nearly straight up
    flying(ball, centre + game.human.width / 2 - 2, game.human.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()
    assert ball.vx > 3  # right edge: steep to the right
    assert ball.vx**2 + ball.vy**2 == pytest.approx(config.BALL_SPEED**2)


def test_lost_ball_counts_against_its_owner_and_goes_to_a_random_player() -> None:
    new_owners = set()
    for seed in range(20):
        game = Game(seed=seed)
        park_robot_ball(game)
        ball = ball_of(game, 0)
        flying(ball, 50, config.SCREEN_HEIGHT + 20, 0, 3, ROBOT)
        game.update()
        assert game.drops == {HUMAN: 0, ROBOT: 1}
        assert ball.waiting
        new_owners.add(ball.owner)
    assert new_owners == {HUMAN, ROBOT}


def test_lost_ball_goes_to_the_same_player_for_the_same_seed() -> None:
    def owners(seed: int) -> list[str]:
        game = Game(seed=seed)
        park_robot_ball(game)
        out = []
        for _ in range(10):
            ball = ball_of(game, 0)
            flying(ball, 50, config.SCREEN_HEIGHT + 20, 0, 3, HUMAN)
            game.update()
            out.append(ball.owner)
        return out

    assert owners(5) == owners(5)


def test_without_a_robot_lost_balls_come_back_to_the_human() -> None:
    game = Game(robot_strategy=None)
    ball = game.balls[0]
    for _ in range(5):
        flying(ball, 50, config.SCREEN_HEIGHT + 20, 0, 3, HUMAN)
        game.update()
        assert ball.waiting and ball.owner == HUMAN


def test_waiting_ball_follows_paddle_until_space() -> None:
    game = Game(lost_ball_to=HUMAN)
    park_robot_ball(game)
    ball = ball_of(game, 0)
    for _ in range(30):
        game.update(LEFT)
    assert ball.waiting
    assert ball.x == pytest.approx(game.human.centre_x)
    game.update(launch_pressed=True)
    assert not ball.waiting


def test_two_waiting_balls_sit_side_by_side_and_launch_one_per_press() -> None:
    game = Game()
    park_robot_ball(game)
    robot_ball = ball_of(game, 1)
    game._put_on_paddle(robot_ball, HUMAN)
    game.update()
    a, b = game.waiting_balls(HUMAN)
    assert a.x != b.x
    assert (a.x + b.x) / 2 == pytest.approx(game.human.centre_x)
    game.update(launch_pressed=True)
    assert len(game.waiting_balls(HUMAN)) == 1


def test_robot_balls_launch_after_delay() -> None:
    game = Game()
    robot_ball = ball_of(game, 1)
    delay = round(config.ROBOT_RELAUNCH_DELAY_S * config.FPS)
    for _ in range(delay):
        game.update()
    assert robot_ball.waiting
    game.update()
    assert not robot_ball.waiting


def test_robot_sweeps_full_width() -> None:
    game = Game()
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
        ball = ball_of(game, 0)
        out = []
        for _ in range(3):
            ball.waiting = True
            game.update(STAY, launch_pressed=True)
            out.append((ball.vx, ball.vy))
        return out

    assert launch_velocities(1) == launch_velocities(1)
    assert launch_velocities(1) != launch_velocities(2)


def test_bad_lost_ball_setting_is_rejected() -> None:
    with pytest.raises(ValueError):
        Game(lost_ball_to="nobody")


def test_score_text() -> None:
    scores = {HUMAN: 20, ROBOT: 14}
    assert score_text(scores, "shared") == "Team: 34"
    assert score_text(scores, "split") == "You: 20 · Robot: 14 · Total: 34"
    assert score_text(scores, "split", "Pip") == "You: 20 · Pip: 14 · Total: 34"
    with pytest.raises(ValueError):
        score_text(scores, "other")


def test_start_screen_freezes_until_space_and_the_timer_starts_then() -> None:
    events = []
    game = Game(round_seconds=1, wait_for_launch=True, listeners=[lambda g, e, d: events.append(e)])
    robot_x = game.robot.x
    for _ in range(3 * config.FPS):
        game.update(LEFT)
    assert not game.started and game.tick == 0 and not game.over
    assert game.robot.x == robot_x and game.human.x == config.HUMAN_START_X
    assert game.seconds_left == 1
    game.update(launch_pressed=True)
    assert game.started and "play_started" in events
    assert not ball_of(game, 0).waiting  # the first Space also launches the ball
    assert ball_of(game, 1).waiting  # the robot's waits its usual delay
