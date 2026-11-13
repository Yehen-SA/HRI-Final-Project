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
from pathlib import Path

# Stop pygame printing its banner on import.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import config  # noqa: E402  (must come after the banner setting)
import engine  # noqa: E402
import session  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HRI Breakout: human + robot")
    parser.add_argument("--free-play", action="store_true", help="play games without surveys")
    parser.add_argument("--pid", help="participant ID (skips the ID screen)")
    parser.add_argument("--autoplay", action="store_true", help="answer and play automatically")
    parser.add_argument("--round-seconds", type=float, help="length of every round (testing)")
    parser.add_argument("--log-dir", type=Path, help="where to write logs (default: logs/)")
    parser.add_argument("--max-frames", type=int, help="quit after this many frames (tests)")
    args = parser.parse_args(argv)

    if args.free_play:
        asyncio.run(engine.run(max_frames=args.max_frames, log_dir=args.log_dir))
        return 0
    seconds = args.round_seconds
    asyncio.run(
        session.run_session(
            log_dir=args.log_dir,
            autoplay=args.autoplay,
            round_seconds=seconds or config.ROUND_SECONDS,
            practice_seconds=seconds or config.PRACTICE_SECONDS,
            participant_id=args.pid,
            max_frames=args.max_frames,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
