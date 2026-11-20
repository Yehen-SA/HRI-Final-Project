"""Per-round statistics, collected from game events.

Use as a game listener:

    stats = RoundStats()
    game = Game(listeners=[stats])
    ... play ...
    stats.summary()   # dict of results, for the log

Every per-player number is kept for both "human" and "robot". To add a measure: count it in
`__call__` (from an event, or every frame in `_every_frame`), then add a row to `ROWS`.

Taking the other player's ball (engine.Game._hit_paddle):
  - steal:  both paddles were under the ball (the owner could have returned it)
  - rescue: only the taker's paddle was there (the owner couldn't)
  - prompted rescue: a rescue of a ball the robot let go on purpose and asked for help with
Rates divide by the chances the player had, so a robot that misses more (more chances to
rescue) or catches more (more chances to steal) doesn't skew them:
  - steal rate  = steals / (the other's balls that reached the other's paddle)
  - rescue rate = rescues / (the other's balls the other couldn't reach)
"""

from typing import Any

import config
from engine import HUMAN, ROBOT, Game

PLAYERS = (HUMAN, ROBOT)

# Rows of the per-player stats table: (key in summary()["players"][player], label in the log).
ROWS = [
    ("score", "Score (total)"),
    ("points_bricks", "Points from bricks"),
    ("points_rules", "Points from rules (bonuses / penalties)"),
    ("bricks_broken", "Bricks broken"),
    ("paddle_hits", "Paddle hits (all)"),
    ("own_catches", "Own balls caught"),
    ("steals_made", "Steals made (took the other's ball while they were under it)"),
    ("steal_chances", "Steal chances (the other's balls that reached the other's paddle)"),
    ("steal_rate", "Steal rate"),
    ("balls_stolen", "Own balls stolen by the other player"),
    ("rescues_made", "Rescues made (saved the other's ball they couldn't reach)"),
    ("rescues_prompted", "  of which prompted (the robot asked for help)"),
    ("rescues_unprompted", "  of which unprompted"),
    ("rescue_chances", "Rescue chances (the other's balls the other couldn't reach)"),
    ("rescue_rate", "Rescue rate (all)"),
    ("prompted_rescue_rate", "Prompted rescue rate (rescued / help requests)"),
    ("unprompted_rescue_rate", "Unprompted rescue rate"),
    ("balls_rescued", "Own balls rescued by the other player"),
    ("balls_lost", "Balls lost"),
    ("balls_received", "Lost balls given to this player"),
    ("possession_s", "Time holding a ball in flight (s, summed over balls)"),
    ("waiting_s", "Time balls waited on this paddle (s)"),
    ("launch_delay_mean_s", "Launch delay, mean (s)"),
    ("launch_delay_median_s", "Launch delay, median (s)"),
    ("paddle_distance_px", "Paddle distance moved (px)"),
    ("moving_s", "Time paddle moving (s)"),
    ("still_s", "Time paddle still (s)"),
    ("powerups_caught", "Power-ups caught"),
]

# Events copied into the timeline (ticks and brick points are left out: too many).
TIMELINE_EVENTS = {
    "ball_launched",
    "paddle_hit",
    "steal",
    "rescue",
    "help_request",
    "brick_broken",
    "points",
    "ball_lost",
    "ball_given",
    "powerup_spawned",
    "powerup_caught",
    "powerup_missed",
    "round_end",
}


def mean(values: list[int]) -> float:
    return sum(values) / len(values)


def median(values: list[int]) -> float:
    """(The statistics module isn't available in the browser build.)"""
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def _rate(count: int, chances: int) -> float | None:
    """count / chances to 3 decimals, or None (no chances) so it isn't mistaken for 0."""
    return round(count / chances, 3) if chances > 0 else None


def _secs(frames: int) -> float:
    return round(frames / config.FPS, 2)


class RoundStats:
    def __init__(self) -> None:
        zero = dict.fromkeys(PLAYERS, 0)
        self.bricks_broken = dict(zero)
        self.paddle_hits = dict(zero)
        self.steals_made = dict(zero)
        self.balls_stolen = dict(zero)
        self.rescues_made = dict(zero)
        self.rescues_prompted = dict(zero)
        self.balls_rescued = dict(zero)
        self.help_requests = 0  # balls the robot let go on purpose and asked for help with
        self.robot_lines: dict[str, int] = {}  # voice lines spoken, per trigger
        self.balls_received = dict(zero)
        self.powerups_caught = dict(zero)
        self.possession_frames = dict(zero)
        self.waiting_frames = dict(zero)
        self.moving_frames = dict(zero)
        self.still_frames = dict(zero)
        self.paddle_distance = {p: 0.0 for p in PLAYERS}
        self.launch_delays: dict[str, list[int]] = {p: [] for p in PLAYERS}
        self.overlap_frames = 0
        self.max_balls = 0
        self.timeline: list[dict[str, Any]] = []
        self._waiting_since: dict[int, int] = {}  # ball id -> tick it started waiting
        self._last_x: dict[str, float] = {}
        self.game: Game | None = None

    # --- Listener ---

    def __call__(self, game: Game, event: str, data: dict[str, Any]) -> None:
        self.game = game
        if event == "round_start":
            for ball in game.balls:
                self._waiting_since[ball.id] = 0
            self._last_x = {p: paddle.x for p, paddle in game.paddles.items()}
        elif event == "tick":
            self._every_frame(game)
        elif event == "brick_broken":
            self.bricks_broken[data["ball"].owner] += 1
        elif event == "paddle_hit":
            self.paddle_hits[data["paddle"].owner] += 1
        elif event == "steal":
            self.steals_made[data["paddle"].owner] += 1
            self.balls_stolen[data["from_player"]] += 1
        elif event == "rescue":
            self.rescues_made[data["paddle"].owner] += 1
            self.balls_rescued[data["from_player"]] += 1
            if data["prompted"]:
                self.rescues_prompted[data["paddle"].owner] += 1
        elif event == "help_request":
            self.help_requests += 1
        elif event == "ball_given":
            self.balls_received[data["player"]] += 1
            self._waiting_since[data["ball"].id] = game.tick
        elif event == "ball_launched":
            ball = data["ball"]
            since = self._waiting_since.pop(ball.id, None)
            if since is not None:
                self.launch_delays[ball.owner].append(game.tick - since)
        elif event == "powerup_caught":
            self.powerups_caught[data["paddle"].owner] += 1

        if event in TIMELINE_EVENTS and not (event == "points" and data["reason"] == "bricks"):
            self.timeline.append(self._timeline_row(game, event, data))

    def robot_said(self, trigger: str, text: str) -> None:
        """The persona spoke a line (pass as RobotPersona(on_say=...))."""
        self.robot_lines[trigger] = self.robot_lines.get(trigger, 0) + 1
        self.note("robot_said", "robot", f"{text} ({trigger})")

    def note(self, event: str, player: str = "", detail: str = "") -> None:
        """Add something else to the timeline (e.g. what the robot said)."""
        tick = self.game.tick if self.game else 0
        self.timeline.append({"t": _secs(tick), "event": event, "player": player, "detail": detail})

    def _every_frame(self, game: Game) -> None:
        for ball in game.balls:
            if ball.waiting:
                self.waiting_frames[ball.owner] += 1
            else:
                self.possession_frames[ball.owner] += 1
        self.max_balls = max(self.max_balls, len(game.balls))
        for player, paddle in game.paddles.items():
            moved = abs(paddle.x - self._last_x.get(player, paddle.x))
            self._last_x[player] = paddle.x
            self.paddle_distance[player] += moved
            if moved > 0:
                self.moving_frames[player] += 1
            else:
                self.still_frames[player] += 1
        if game.robot is not None and game.human.rect.colliderect(game.robot.rect):
            self.overlap_frames += 1

    @staticmethod
    def _timeline_row(game: Game, event: str, data: dict[str, Any]) -> dict[str, Any]:
        player, detail = "", ""
        if event in ("ball_launched", "ball_lost"):
            ball = data["ball"]
            player, detail = ball.owner, f"ball {ball.id} at x={ball.x:.0f}"
        elif event == "paddle_hit":
            player, detail = data["paddle"].owner, f"ball {data['ball'].id}"
        elif event == "steal":
            player = data["paddle"].owner
            detail = f"ball {data['ball'].id} from {data['from_player']}"
        elif event == "rescue":
            player = data["paddle"].owner
            prompted = "prompted" if data["prompted"] else "unprompted"
            detail = f"ball {data['ball'].id} from {data['from_player']} ({prompted})"
        elif event == "help_request":
            player, detail = "robot", f"let ball {data['ball'].id} go, asked for help"
        elif event == "brick_broken":
            brick = data["brick"]
            player = data["ball"].owner
            detail = f"row {brick.row} col {brick.col} (+{brick.points})"
        elif event == "points":
            player, detail = data["player"], f"{data['points']:+d} {data['reason']}"
        elif event == "ball_given":
            player, detail = data["player"], f"ball {data['ball'].id}"
        elif event == "powerup_caught":
            player, detail = data["paddle"].owner, data["powerup"].kind
        elif event in ("powerup_spawned", "powerup_missed"):
            detail = data["powerup"].kind
        elif event == "round_end":
            detail = data["reason"]
        return {"t": _secs(game.tick), "event": event, "player": player, "detail": detail}

    # --- Results ---

    def summary(self) -> dict[str, Any]:
        """Everything measured this round, as plain data (for the log and its JSON block)."""
        game = self.game
        assert game is not None, "RoundStats was never attached to a game"
        players: dict[str, dict[str, Any]] = {}
        own_catches = {
            p: self.paddle_hits[p] - self.steals_made[p] - self.rescues_made[p] for p in PLAYERS
        }
        for p in PLAYERS:
            other = ROBOT if p == HUMAN else HUMAN
            steal_chances = own_catches[other] + self.steals_made[p]
            rescue_chances = self.rescues_made[p] + game.drops[other]
            prompted_chances = self.help_requests if p == HUMAN else 0
            unprompted = self.rescues_made[p] - self.rescues_prompted[p]
            by_reason = game.points_by_reason[p]
            delays = self.launch_delays[p]
            players[p] = {
                "score": game.scores[p],
                "points_bricks": by_reason.get("bricks", 0),
                "points_rules": sum(v for k, v in by_reason.items() if k != "bricks"),
                "points_by_reason": dict(by_reason),
                "bricks_broken": self.bricks_broken[p],
                "paddle_hits": self.paddle_hits[p],
                "own_catches": own_catches[p],
                "steals_made": self.steals_made[p],
                "steal_chances": steal_chances,
                "steal_rate": _rate(self.steals_made[p], steal_chances),
                "balls_stolen": self.balls_stolen[p],
                "rescues_made": self.rescues_made[p],
                "rescues_prompted": self.rescues_prompted[p],
                "rescues_unprompted": unprompted,
                "rescue_chances": rescue_chances,
                "rescue_rate": _rate(self.rescues_made[p], rescue_chances),
                "prompted_rescue_rate": _rate(self.rescues_prompted[p], prompted_chances),
                "unprompted_rescue_rate": _rate(unprompted, rescue_chances - prompted_chances),
                "balls_rescued": self.balls_rescued[p],
                "balls_lost": game.drops[p],
                "balls_received": self.balls_received[p],
                "possession_s": _secs(self.possession_frames[p]),
                "waiting_s": _secs(self.waiting_frames[p]),
                "launch_delay_mean_s": _secs(round(mean(delays))) if delays else None,
                "launch_delay_median_s": _secs(round(median(delays))) if delays else None,
                "paddle_distance_px": round(self.paddle_distance[p]),
                "moving_s": _secs(self.moving_frames[p]),
                "still_s": _secs(self.still_frames[p]),
                "powerups_caught": self.powerups_caught[p],
            }
        total = game.scores[HUMAN] + game.scores[ROBOT]
        return {
            "duration_s": _secs(game.tick),
            "end_reason": game.end_reason or "unfinished",
            "team_score": total,
            "robot_share_of_score": round(game.scores[ROBOT] / total, 3) if total else None,
            "bricks_broken": len(game.bricks) - game.bricks_left,
            "bricks_left": game.bricks_left,
            "paddles_overlapping_s": _secs(self.overlap_frames),
            "help_requests": self.help_requests,
            "robot_lines_by_trigger": dict(sorted(self.robot_lines.items())),
            "max_balls_in_play": self.max_balls,
            "players": players,
        }
