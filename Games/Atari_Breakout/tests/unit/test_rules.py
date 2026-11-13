"""Optional rules in rules.py, and the engine's event system they rely on."""

import config
import rules
from engine import EVENTS, HUMAN, ROBOT, Game
from entities import Ball
from robot_strategies import Strategy


def game_with(*active: rules.Rule, **kwargs) -> Game:
    kwargs.setdefault("robot_strategy", Strategy.SWEEP)
    game = Game(rules=list(active), **kwargs)
    next(b for b in game.balls if b.id == 1).launch_tick = 10**9  # park the robot's ball
    return game


def flying(ball: Ball, x: float, y: float, vx: float, vy: float, owner: str) -> None:
    ball.waiting = False
    ball.x, ball.y, ball.vx, ball.vy = x, y, vx, vy
    ball.owner = owner


def lose(game: Game, owner: str) -> None:
    flying(game.balls[0], 50, config.SCREEN_HEIGHT + 20, 0, 3, owner)
    game.update()


def steal_by_robot(game: Game) -> None:
    game.human.x = 0
    ball = game.balls[0]
    flying(ball, game.robot.centre_x, game.robot.y - ball.radius - 1, 0, 3, HUMAN)
    game.update()


def test_example_rules_are_off_by_default() -> None:
    assert rules.RULES and not rules.enabled_rules()


def test_every_engine_event_has_a_rule_hook() -> None:
    for event in EVENTS:
        assert hasattr(rules.Rule, f"on_{event}")


def test_listeners_get_events_with_their_data() -> None:
    seen = []
    game = Game(
        robot_strategy=Strategy.SWEEP, rules=[], listeners=[lambda e, d: seen.append((e, d))]
    )
    steal_by_robot(game)
    names = [e for e, _ in seen]
    assert names[0] == "round_start"
    assert "steal" in names and "paddle_hit" in names
    for event, data in seen:
        assert set(data) == set(EVENTS[event])


def test_lost_ball_penalty() -> None:
    game = game_with(rules.LostBallPenalty(points=3))
    game.scores[ROBOT] = 10
    lose(game, ROBOT)
    assert game.scores[ROBOT] == 7
    assert game.points_by_reason[ROBOT] == {"lost ball penalty": -3}


def test_lost_ball_penalty_never_goes_below_zero() -> None:
    game = game_with(rules.LostBallPenalty(points=3))
    game.scores[HUMAN] = 1
    lose(game, HUMAN)
    assert game.scores[HUMAN] == 0
    lose(game, HUMAN)
    assert game.scores[HUMAN] == 0


def test_steal_bonus() -> None:
    game = game_with(rules.StealBonus(points=2))
    steal_by_robot(game)
    assert game.scores == {HUMAN: 0, ROBOT: 2}
    assert game.points_by_reason[ROBOT] == {"steal bonus": 2}


def test_multiball_powerup_drops_and_adds_a_ball_when_caught() -> None:
    game = game_with(rules.MultiBallPowerUp(drop_chance=1.0))
    brick = game.bricks[-1]  # bottom row, closest to the paddles
    ball = game.balls[0]
    flying(ball, brick.rect.centerx, brick.rect.bottom + ball.radius + 1, 0, -3, HUMAN)
    game.update()
    assert len(game.powerups) == 1
    game.human.x = game.powerups[0].rect.centerx - game.human.width / 2
    ball.waiting, ball.vx, ball.vy = True, 0, 0  # keep the first ball out of the way
    for _ in range(300):
        game.update()
        if not game.powerups:
            break
    assert len(game.balls) == game.base_ball_count + 1
    extra = game.balls[-1]
    assert extra.owner == HUMAN and not extra.waiting


def test_extra_balls_vanish_when_lost() -> None:
    game = game_with()
    extra = game.spawn_ball(HUMAN, 100, 300)
    flying(extra, 50, config.SCREEN_HEIGHT + 20, 0, 3, HUMAN)
    game.update()
    assert extra not in game.balls
    assert len(game.balls) == game.base_ball_count
    assert game.drops[HUMAN] == 1


def test_brick_points_are_recorded_by_reason() -> None:
    game = game_with()
    brick = game.bricks[0]
    ball = game.balls[0]
    flying(ball, brick.rect.centerx, brick.rect.bottom + ball.radius + 1, 0, -3, HUMAN)
    game.update()
    assert game.points_by_reason[HUMAN] == {"bricks": 7}


def test_round_end_is_announced_once_with_a_reason() -> None:
    ends = []
    game = Game(
        round_seconds=0.1, rules=[], listeners=[lambda e, d: e == "round_end" and ends.append(d)]
    )
    for _ in range(20):
        game.update()
    game.end("quit")
    assert ends == [{"reason": "timer"}]
    assert game.end_reason == "timer"
