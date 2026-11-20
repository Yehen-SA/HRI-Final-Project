"""The study session: participant ID, then three stages.

  Stage 1  pre-game questions (pre_questions.py), then how-to-play pages
  Stage 2  practice round (no robot), then for each robot in the participant's order:
           round intro, a round with that robot, post-round questions (post_questions.py)
  Stage 3  final questions (post_questions.FINAL_QUESTIONS; currently none), then the
           debrief and end screen

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
import web
from actions import LEFT, RIGHT, STAY
from assignment import conditions_for
from engine import Game
from human_controls import LAUNCH_KEY, QUIT_KEY, read_human_action
from post_questions import FINAL_QUESTIONS, POST_ROUND_QUESTIONS
from pre_questions import PRE_QUESTIONS
from robot_persona import RobotPersona, persona_config
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
    """Plays one round: a start screen (the robot introduces itself), play from the first
    Space, and when it ends, waits for Space before moving on."""

    def __init__(
        self,
        game: Game,
        over_message: str,
        autoplay: bool = False,
        persona: RobotPersona | None = None,
        start_message: str = "",
    ) -> None:
        self.game = game
        self.over_message = over_message
        self.start_message = start_message
        self.autoplay = autoplay
        self.persona = persona
        self.done = False
        self._space = False
        self._font = ui.font(30)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == LAUNCH_KEY:
            self._space = True

    def update(self, keys: Any) -> None:
        if self.persona is not None:
            self.persona.update(self.game)
        if self.game.over:
            if self._space or self.autoplay:
                self.done = True
                if self.persona is not None:
                    self.persona.stop()
        elif self.autoplay:
            self.game.update(autoplay_action(self.game), launch_pressed=True)
        else:
            self.game.update(read_human_action(keys.__getitem__), self._space)
        self._space = False

    def draw(self, surface: pygame.Surface) -> None:
        self.game.draw(surface, self._font, end_overlay=False)
        if self.persona is not None and self.game.robot is not None:
            self.persona.draw(surface, self.game.robot.rect)
        if not self.game.started and self.start_message:
            margin = 80
            y = round(config.PLAY_BOTTOM * 0.42)
            width = config.SCREEN_WIDTH - 2 * margin
            ui.draw_text_block(surface, self.start_message, 34, margin, y, width, center=True)
        if self.game.over:
            ui.draw_overlay(surface, [self.over_message, "", self.game.hud_score_text()])


class MessageScreen:
    """A page of text. Done on Enter or Space (or straight away in autoplay)."""

    def __init__(
        self,
        message: str,
        autoplay: bool = False,
        closes_game: bool = False,
        on_d: Any = None,
    ) -> None:
        self.message = message
        self.done = autoplay
        self.closes_game = closes_game  # the end screen: Enter/Space quits
        self.on_d = on_d  # called when D is pressed (re-download the log in the browser)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_d and self.on_d:
            self.on_d()
        elif event.type == pygame.KEYDOWN and event.key in (
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
        identities = [persona_config.identity_for_round(n) for n in range(1, rounds + 1)]
        context = {
            "participant_id": pid,
            "score_mode": conditions.score_mode,
            # robot_1_name, robot_2_name: for questions that compare the robots
            **{f"robot_{n}_name": ident.name for n, ident in enumerate(identities, start=1)},
            "rounds": rounds,
            "practice_seconds": round(self.practice_seconds),
            "round_minutes": max(1, math.ceil(self.round_seconds / 60)),
        }
        self.log = log = SessionLog.create(pid, self.log_dir)
        log.write_participant(
            conditions.as_log() | {"robot_names": [ident.name for ident in identities]}
        )
        log.write_settings()

        # Stage 1: pre-game questions and instructions
        pre = self.survey("Before the game", PRE_QUESTIONS, context)
        yield pre
        log.write_answers("Stage 1: pre-game questions", pre.answers(), key="pre")
        if pre.declined:
            self.status = "declined"
            log.finish("declined")
            yield self.end_screen(text.DECLINED)
            return
        yield self.survey("How to play", text.INSTRUCTIONS, context)

        # Stage 2: practice, then one round per robot with questions after each
        yield from self.play_round(
            {"title": "Practice round", "round_kind": "practice", "robot": "none"},
            None,
            self.practice_seconds,
            conditions.score_mode,
            text.PRACTICE_OVER,
            start_message=text.PRACTICE_START.format_map(context),
        )
        for number, strategy in enumerate(conditions.robot_order, start=1):
            identity = identities[number - 1]
            round_context = context | {
                "round_number": number,
                "robot": strategy.name,
                "robot_name": identity.name,
                "robot_colour": identity.colour_name,
            }
            yield from self.play_round(
                {
                    "title": f"Round {number}: {identity.name} (robot {strategy.name})",
                    "round_kind": "main",
                    "round_number": number,
                    "robot": strategy.name,
                    "robot_name": identity.name,
                },
                strategy,
                self.round_seconds,
                conditions.score_mode,
                text.ROUND_OVER,
                identity,
                start_message=text.ROUND_START.format_map(round_context),
            )
            post = self.survey(f"After round {number}", POST_ROUND_QUESTIONS, round_context)
            yield post
            log.write_answers(
                f"Round {number}: post-round questions ({identity.name}, {strategy.name})",
                post.answers(),
                key=f"post_round_{number}",
            )

        # Stage 3: final questions (skipped while FINAL_QUESTIONS is empty), then the debrief
        if FINAL_QUESTIONS:
            final = self.survey("Final questions", FINAL_QUESTIONS, context)
            yield final
            log.write_answers("Stage 3: final questions", final.answers(), key="final")
        self.status = "complete"
        log.finish("complete")
        yield self.end_screen(text.END)

    def end_screen(self, message: str) -> "MessageScreen":
        """The last screen: in the browser, explains the downloaded log (D downloads again)."""
        assert self.log is not None
        if web.IN_BROWSER:
            message += "\n\n" + text.END_WEB_LOG.format(log_name=self.log.path.name)
            return MessageScreen(message, self.autoplay, closes_game=True, on_d=self.log.download)
        if config.SHOW_LOG_PATH_AT_END:
            message += "\n\n" + text.END_SEND_LOG.format(log_path=self.log.path)
        return MessageScreen(message, self.autoplay, closes_game=True)

    def play_round(
        self,
        info: dict[str, Any],
        strategy: Strategy | None,
        seconds: float,
        score_mode: str,
        over_message: str,
        identity: persona_config.Identity | None = None,
        start_message: str = "",
    ) -> Generator[Screen, None, None]:
        """Play a round (with the robot `identity`, if there's a robot), then log it."""
        assert self.log is not None
        stats = RoundStats()
        listeners: list = [stats]
        persona = None
        identity = identity or persona_config.FREE_PLAY_IDENTITY
        if strategy is not None:
            persona = RobotPersona(
                on_say=stats.robot_said,
                identity=identity,
            )
            listeners.append(persona)
        game = Game(
            score_mode=score_mode,
            seed=config.SEED,  # same start every round
            round_seconds=seconds,
            robot_strategy=strategy,
            listeners=listeners,
            robot_name=identity.name,
            robot_colour=identity.body,
            wait_for_launch=True,
        )
        info = info | {"score_mode": score_mode, "seed": config.SEED}
        self._open_round = (game, stats, info)
        yield RoundScreen(game, over_message, self.autoplay, persona, start_message)
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
