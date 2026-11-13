"""The study session: participant ID, then three stages.

  Stage 1  pre-game questions (pre_questions.py), then how-to-play pages
  Stage 2  practice round (no robot), then for each robot in the participant's order:
           round intro, a round with that robot, post-round questions (post_questions.py)
  Stage 3  final questions (post_questions.py), then the end screen

The order is written as a generator in `Session.flow()`: each `yield` shows a screen until
it's done, so changing the order means editing that one method. Everything is logged as it
happens (session_log.py). Esc pauses; Esc again quits, and the log is marked "aborted".
"""

import asyncio
import math
from collections.abc import Generator
from pathlib import Path
from typing import Any, Protocol

import pygame

import config
import session_text as text
import ui
from actions import LEFT, RIGHT, STAY
from assignment import conditions_for
from engine import Game
from human_controls import LAUNCH_KEY, QUIT_KEY, read_human_action
from post_questions import FINAL_QUESTIONS, POST_ROUND_QUESTIONS
from pre_questions import PRE_QUESTIONS
from robot_strategies import Strategy
from session_log import SessionLog
from stats import RoundStats
from survey_screen import SurveyScreen


class Screen(Protocol):
    done: bool

    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, keys: Any) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...


def autoplay_action(game: Game) -> str:
    """A simple stand-in player for autoplay: follows the lowest falling ball."""
    falling = [b for b in game.balls if not b.waiting and b.vy > 0]
    target = max(falling, key=lambda b: b.y).x if falling else config.SCREEN_WIDTH / 4
    if abs(target - game.human.centre_x) < 6:
        return STAY
    return LEFT if target < game.human.centre_x else RIGHT


class RoundScreen:
    """Plays one round; when it ends, waits for Space before moving on."""

    def __init__(self, game: Game, over_message: str, autoplay: bool = False) -> None:
        self.game = game
        self.over_message = over_message
        self.autoplay = autoplay
        self.done = False
        self._space = False
        self._font = ui.font(30)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == LAUNCH_KEY:
            self._space = True

    def update(self, keys: Any) -> None:
        if self.game.over:
            if self._space or self.autoplay:
                self.done = True
        elif self.autoplay:
            self.game.update(autoplay_action(self.game), launch_pressed=True)
        else:
            self.game.update(read_human_action(keys.__getitem__), self._space)
        self._space = False

    def draw(self, surface: pygame.Surface) -> None:
        self.game.draw(surface, self._font, end_overlay=False)
        if self.game.over:
            ui.draw_overlay(surface, [self.over_message, "", self.game.hud_score_text()])


class MessageScreen:
    """A page of text. Done on Enter or Space (or straight away in autoplay)."""

    def __init__(self, message: str, autoplay: bool = False, closes_game: bool = False) -> None:
        self.message = message
        self.done = autoplay
        self.closes_game = closes_game  # the end screen: Enter/Space quits

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
        ):
            self.done = True

    def update(self, keys: Any) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(config.COLOR_BG)
        margin = 60
        ui.draw_text_block(surface, self.message, 30, margin, 120, config.SCREEN_WIDTH - 2 * margin)


class Session:
    def __init__(
        self,
        log_dir: Path | None = None,
        autoplay: bool = False,
        round_seconds: float = config.ROUND_SECONDS,
        practice_seconds: float = config.PRACTICE_SECONDS,
        participant_id: str | None = None,
    ) -> None:
        self.log_dir = log_dir
        self.autoplay = autoplay
        self.round_seconds = round_seconds
        self.practice_seconds = practice_seconds
        self.participant_id = participant_id
        self.log: SessionLog | None = None
        self.status = "aborted"
        self._open_round: tuple[Game, RoundStats, dict[str, Any]] | None = None

    def survey(self, title: str, questions: list, context: dict[str, Any]) -> SurveyScreen:
        return SurveyScreen(title, questions, context)

    # --- The order of the session ---

    def flow(self) -> Generator[Screen, None, None]:
        # Participant ID (skipped if given on the command line)
        pid = self.participant_id
        while not pid:
            id_screen = self.survey("Participant ID", [text.PARTICIPANT_ID], {})
            yield id_screen
            pid = str(id_screen.values.get("participant_id") or "").strip()
        conditions = conditions_for(pid)
        rounds = len(conditions.robot_order)
        context = {
            "participant_id": pid,
            "score_mode": conditions.score_mode,
            "robot_name": config.ROBOT_NAME,
            "rounds": rounds,
            "practice_seconds": round(self.practice_seconds),
            "round_minutes": max(1, math.ceil(self.round_seconds / 60)),
        }
        self.log = log = SessionLog.create(pid, self.log_dir)
        log.write_participant(conditions.as_log())
        log.write_settings()

        # Stage 1: pre-game questions and instructions
        pre = self.survey("Before the game", PRE_QUESTIONS, context)
        yield pre
        log.write_answers("Stage 1: pre-game questions", pre.answers(), key="pre")
        if pre.declined:
            self.status = "declined"
            log.finish("declined")
            yield MessageScreen(text.DECLINED, self.autoplay, closes_game=True)
            return
        yield self.survey("How to play", text.INSTRUCTIONS, context)

        # Stage 2: practice, then one round per robot with questions after each
        yield from self.play_round(
            {"title": "Practice round", "round_kind": "practice", "robot": "none"},
            None,
            self.practice_seconds,
            conditions.score_mode,
            text.PRACTICE_OVER,
        )
        for number, strategy in enumerate(conditions.robot_order, start=1):
            round_context = context | {"round_number": number, "robot": strategy.name}
            yield self.survey(f"Round {number}", text.ROUND_INTRO, round_context)
            yield from self.play_round(
                {
                    "title": f"Round {number}: robot {strategy.name}",
                    "round_kind": "main",
                    "round_number": number,
                    "robot": strategy.name,
                },
                strategy,
                self.round_seconds,
                conditions.score_mode,
                text.ROUND_OVER,
            )
            post = self.survey(f"After round {number}", POST_ROUND_QUESTIONS, round_context)
            yield post
            log.write_answers(
                f"Round {number}: post-round questions ({strategy.name})",
                post.answers(),
                key=f"post_round_{number}",
            )

        # Stage 3: final questions
        final = self.survey("Final questions", FINAL_QUESTIONS, context)
        yield final
        log.write_answers("Stage 3: final questions", final.answers(), key="final")
        self.status = "complete"
        log.finish("complete")
        end = text.END
        if config.SHOW_LOG_PATH_AT_END:
            end += "\n\n" + text.END_SEND_LOG.format(log_path=log.path)
        yield MessageScreen(end, self.autoplay, closes_game=True)

    def play_round(
        self,
        info: dict[str, Any],
        strategy: Strategy | None,
        seconds: float,
        score_mode: str,
        over_message: str,
    ) -> Generator[Screen, None, None]:
        """Play a round, then write it to the log."""
        assert self.log is not None
        stats = RoundStats()
        game = Game(
            score_mode=score_mode,
            seed=config.SEED,  # same start every round
            round_seconds=seconds,
            robot_strategy=strategy,
            listeners=[stats],
        )
        info = info | {"score_mode": score_mode, "seed": config.SEED}
        self._open_round = (game, stats, info)
        yield RoundScreen(game, over_message, self.autoplay)
        self._open_round = None
        self.log.write_round(info, stats)

    # --- Quitting early ---

    def abort(self) -> None:
        """Save what we have and mark the log aborted (Esc twice, window closed, or a crash)."""
        if self.log is None or self.log.finished:
            return
        if self._open_round is not None:
            game, stats, info = self._open_round
            game.end("quit")
            self.log.write_round(info, stats)
            self._open_round = None
        self.log.finish("aborted")


async def run_session(
    log_dir: Path | None = None,
    autoplay: bool = False,
    round_seconds: float = config.ROUND_SECONDS,
    practice_seconds: float = config.PRACTICE_SECONDS,
    participant_id: str | None = None,
    max_frames: int | None = None,
) -> Session:
    """Open the window and run a whole session. Returns the session (for tests)."""
    pygame.init()
    surface = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.WINDOW_TITLE)
    clock = pygame.time.Clock()
    session = Session(log_dir, autoplay, round_seconds, practice_seconds, participant_id)
    flow = session.flow()
    screen: Screen | None = next(flow)
    paused = False
    frames = 0
    try:
        while screen is not None and (max_frames is None or frames < max_frames):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    screen = None
                    break
                if event.type == pygame.KEYDOWN and event.key == QUIT_KEY:
                    is_end = isinstance(screen, MessageScreen) and screen.closes_game
                    if paused or is_end:
                        screen = None
                        break
                    paused = True
                    continue
                if paused:
                    if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_SPACE,
                        pygame.K_RETURN,
                    ):
                        paused = False
                    continue
                screen.handle_event(event)
            if screen is None:
                break
            if autoplay and isinstance(screen, SurveyScreen) and not screen.done:
                screen.auto_answer()
            if not paused:
                screen.update(pygame.key.get_pressed())
            screen.draw(surface)
            if paused:
                ui.draw_overlay(surface, ["Paused", "", "Space: carry on", "Esc: quit the study"])
            pygame.display.flip()
            clock.tick(config.FPS)
            frames += 1
            await asyncio.sleep(0)
            while screen is not None and screen.done:
                screen = next(flow, None)
    finally:
        session.abort()  # does nothing if the log is already finished
        pygame.quit()
    return session
