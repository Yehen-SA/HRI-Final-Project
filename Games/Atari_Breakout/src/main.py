"""Entry point: uv run src/main.py"""

import os

# Stop pygame printing its banner on import.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def main() -> int:
    """Start the game. Will call engine.Game().run() once the engine is implemented."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
