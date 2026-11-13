"""Entry point: uv run src/main.py

Runs the study session by default. Options:
  --free-play          just play games (each one is logged), no surveys
  --pid P07            skip the participant ID screen
  --autoplay           answer and play automatically (for testing)
  --round-seconds N    shorten rounds and the practice round (for testing)
  --log-dir DIR        write logs somewhere other than logs/
  --max-frames N       stop after N frames (for tests)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Stop pygame printing its banner on import.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

# The browser build (pygbag) only loads pygame if main.py imports it directly.
import pygame  # noqa: E402, F401

import config  # noqa: E402  (must come after the banner setting)
import engine  # noqa: E402
import session  # noqa: E402


async def main_async(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="HRI Breakout: human + robot")
    parser.add_argument("--free-play", action="store_true", help="play games without surveys")
    parser.add_argument("--pid", help="participant ID (skips the ID screen)")
    parser.add_argument("--autoplay", action="store_true", help="answer and play automatically")
    parser.add_argument("--round-seconds", type=float, help="length of every round (testing)")
    parser.add_argument("--log-dir", type=Path, help="where to write logs (default: logs/)")
    parser.add_argument("--max-frames", type=int, help="quit after this many frames (tests)")
    args = parser.parse_args(argv)

    if args.free_play:
        await engine.run(max_frames=args.max_frames, log_dir=args.log_dir)
        return
    seconds = args.round_seconds
    await session.run_session(
        log_dir=args.log_dir,
        autoplay=args.autoplay,
        round_seconds=seconds or config.ROUND_SECONDS,
        practice_seconds=seconds or config.PRACTICE_SECONDS,
        participant_id=args.pid,
        max_frames=args.max_frames,
    )


if __name__ == "__main__":
    if sys.platform == "emscripten":
        # Browser (pygbag): a plain asyncio.run, no exit code; the page has no command line.
        asyncio.run(main_async([]))
    else:
        asyncio.run(main_async())
