import config
from actions import ACTIONS, LEFT, RIGHT, STAY
from engine import ROBOT, Game
from robot_agent import Robot
from robot_strategies import STRATEGIES, GoodStrategy, Strategy


def obs(x: float, balls: list | None = None) -> dict:
    return {
        "tick": 0,
        "screen_width": config.SCREEN_WIDTH,
        "screen_height": config.SCREEN_HEIGHT,
        "paddle_y": config.PADDLE_Y,
        "robot_paddle": {"x": x, "y": config.PADDLE_Y, "width": config.PADDLE_WIDTH},
        "human_paddle": {"x": 0, "y": config.PADDLE_Y, "width": config.PADDLE_WIDTH},
        "balls": balls or [],
        "bricks_left": 60,
    }


def ball(x: float, y: float, vx: float, vy: float, ball_id: int = 0) -> dict:
    return {
        "id": ball_id,
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "radius": 7,
        "owner": ROBOT,
        "waiting": False,
    }


def test_every_strategy_is_registered_and_returns_actions() -> None:
    assert set(STRATEGIES) == set(Strategy)
    for strategy in Strategy:
        robot = Robot(strategy)
        for _ in range(50):
            assert robot.get_action(obs(300, [ball(400, 300, 2, 3)])) in ACTIONS


def test_sweep_turns_at_both_edges() -> None:
    robot = Robot(Strategy.SWEEP)
    assert robot.get_action(obs(300)) == RIGHT
    assert robot.get_action(obs(config.SCREEN_WIDTH - config.PADDLE_WIDTH)) == LEFT
    assert robot.get_action(obs(300)) == LEFT
    assert robot.get_action(obs(0)) == RIGHT


def test_landing_prediction_bounces_off_walls() -> None:
    # Falls 100 px at vy=1 while drifting 150 px right from x=750: hits the right wall
    # (x = 793) after 43 px, then travels back 107 px.
    frames, x = GoodStrategy.landing_x(ball(750, 453, 1.5, 1), 560, 800)
    assert frames == 100
    assert abs(x - (793 - 107)) < 1e-6


def test_good_goes_for_the_most_urgent_ball(monkeypatch) -> None:
    monkeypatch.setattr(GoodStrategy, "REACTION_DELAY_FRAMES", 0)
    monkeypatch.setattr(GoodStrategy, "AIM_ERROR_PX", 0)
    monkeypatch.setattr(GoodStrategy, "MISJUDGE_CHANCE", 0)
    robot = Robot(Strategy.GOOD)
    near_left = ball(100, 500, 0, 3, ball_id=0)  # lands soon, far left
    far_right = ball(750, 200, 0, 3, ball_id=1)  # lands later, right
    assert robot.get_action(obs(400, [near_left, far_right])) == LEFT


def test_same_seed_same_moves() -> None:
    def moves(strategy: Strategy, seed: int) -> list[str]:
        game = Game(seed=seed, robot_strategy=strategy)
        out = []
        for _ in range(600):
            game.update(STAY, launch_pressed=game.tick == 0)
            out.append(game.robot.x)
        return out

    for strategy in (Strategy.BAD, Strategy.GOOD):
        assert moves(strategy, 3) == moves(strategy, 3)


def test_good_catches_far_more_than_bad() -> None:
    def drops(strategy: Strategy) -> int:
        total = 0
        for seed in range(3):
            game = Game(
                seed=seed,
                round_seconds=120,  # a full round
                robot_strategy=strategy,
                lost_ball_to=ROBOT,
                help_requests=0,
            )
            while not game.over:
                game.update()
            total += game.drops[ROBOT]
        return total

    assert drops(Strategy.GOOD) * 3 < drops(Strategy.BAD)


def test_no_robot_means_no_robot_paddle_or_ball() -> None:
    game = Game(robot_strategy=None)
    assert game.robot is None
    assert len(game.balls) == 1
    for _ in range(120):
        game.update(launch_pressed=True)
