"""Shared pytest fixtures and configuration.

Tests under tests/unit/ are marked `unit` and tests under tests/e2e/ are marked `e2e`
automatically, so `pytest -m unit` or `pytest -m e2e` runs one set.
"""

from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        suite = item.path.relative_to(TESTS_DIR).parts[0]
        if suite in ("unit", "e2e"):
            item.add_marker(getattr(pytest.mark, suite))
