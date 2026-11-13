"""Compare robot strategies in headless rounds where the human does nothing.

Run from the game folder:  uv run tools/simulate_robot.py [--rounds 5] [--seconds 180]

For each strategy it prints, averaged over the rounds: catches (paddle hits on balls),
drops, catch rate, and the robot's points per minute.
"""

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from engine import ROBOT, Game  # noqa: E402
from robot_strategies import Strategy  # noqa: E402


def simulate(strategy: Strategy, seed: int, seconds: float) -> dict[str, float]:
    game = Game(seed=seed, round_seconds=seconds, robot_strategy=strategy)
    game.human_ball.waiting = True
    game.human_ball.launch_tick = 10**9  # human never launches
    catches = 0
    while not game.over:
        before = (game.robot_ball.vy, game.robot_ball.y)
        game.update()
        ball = game.robot_ball
        if before[0] > 0 and ball.vy < 0 and ball.y > game.robot.y - 3 * ball.radius:
            catches += 1
    minutes = game.tick / 60 / 60
    drops = game.drops[ROBOT]
    return {
        "catches": catches,
        "drops": drops,
        "catch_rate": catches / max(1, catches + drops),
        "points_per_min": game.scores[ROBOT] / minutes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--seconds", type=float, default=180)
    args = parser.parse_args()
    print(f"{'strategy':<8} {'catches':>8} {'drops':>6} {'catch rate':>11} {'points/min':>11}")
    for strategy in Strategy:
        runs = [simulate(strategy, seed, args.seconds) for seed in range(args.rounds)]
        avg = {k: sum(r[k] for r in runs) / len(runs) for k in runs[0]}
        print(
            f"{strategy.name:<8} {avg['catches']:>8.1f} {avg['drops']:>6.1f} "
            f"{avg['catch_rate']:>11.0%} {avg['points_per_min']:>11.1f}"
        )


if __name__ == "__main__":
    main()
