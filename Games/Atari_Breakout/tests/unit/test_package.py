import breakout


def test_package_has_version() -> None:
    assert isinstance(breakout.__version__, str)
