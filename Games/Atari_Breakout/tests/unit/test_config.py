import config


def test_paddle_row_fits_on_screen() -> None:
    assert config.HUD_HEIGHT < config.PADDLE_Y
    assert config.PADDLE_Y + config.PADDLE_HEIGHT <= config.SCREEN_HEIGHT


def test_paddles_start_on_screen() -> None:
    for x in (config.HUMAN_START_X, config.ROBOT_START_X):
        assert 0 <= x
        assert x + config.PADDLE_WIDTH <= config.SCREEN_WIDTH


def test_bricks_sit_above_paddle_row() -> None:
    rows_height = config.BRICK_ROWS * (config.BRICK_HEIGHT + config.BRICK_GAP)
    assert config.BRICK_TOP + rows_height < config.PADDLE_Y


def test_brick_grid_fits_screen_width() -> None:
    grid_width = config.BRICK_COLS * config.BRICK_WIDTH + (config.BRICK_COLS + 1) * config.BRICK_GAP
    assert config.BRICK_WIDTH > 0
    assert grid_width <= config.SCREEN_WIDTH


def test_players_have_different_colours() -> None:
    assert config.COLOR_HUMAN != config.COLOR_ROBOT


def test_balls_start_above_paddle_row() -> None:
    assert config.HUD_HEIGHT < config.PADDLE_Y - 2 * config.BALL_RADIUS


def test_every_brick_row_has_points() -> None:
    assert len(config.BRICK_ROW_POINTS) >= config.BRICK_ROWS


def test_launch_angles_valid() -> None:
    assert 0 < config.LAUNCH_ANGLE_MIN_DEG <= config.LAUNCH_ANGLE_MAX_DEG < 90
    assert 0 < config.MAX_BOUNCE_ANGLE_DEG < 90


def test_score_mode_valid() -> None:
    assert config.SCORE_MODE in ("shared", "split")
