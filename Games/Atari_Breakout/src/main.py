"""Entry point: uv run src/main.py"""

import argparse
import asyncio
import os

# Stop pygame printing its banner on import.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import engine  # noqa: E402  (must come after the banner setting)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HRI Breakout: human + robot")
    parser.add_argument("--max-frames", type=int, help="quit after this many frames (tests)")
    args = parser.parse_args(argv)
    asyncio.run(engine.run(max_frames=args.max_frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
