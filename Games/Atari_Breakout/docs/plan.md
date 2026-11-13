# Build plan: Breakout study game

Status: phase 1 (basic game) done. Round 2 steps 1–6 done; step 7 to do.

## Context

The basic co-op Breakout game (phase 1) is built and committed (`f120df9`) in
`Games/Atari_Breakout/`: two colour-coded balls, a sweeping robot, row points 7/7/4/4/1/1, last
hitter scores, 180 s rounds, headless `Game.update()` with 31 tests. The team has now decided on
seven improvements, to be built **in this order, one commit each**:

1. Two robot AIs (random vs trying properly) as strategies passed to a `Robot` by enum.
2. Clearer scoring: ball colour follows who would score; a lost ball respawns with a random player.
3. A `rules.py` where optional rules (penalties, steal rewards, power-ups) are easy to switch on/off.
4. A structured Markdown log per session with settings, independent variables and outcome stats.
5. In-game pre/post surveys, built from `pre_questions.py` / `post_questions.py`, answers in the log.
6. A robot persona module: sprite under its paddle, expressions, speech bubbles and voice.
7. Restructure into `Atari_Breakout/python_build` with generated `html_build` and `exe_build` packages.

This plan replaces the earlier phase 2 draft (`study.toml`, Supabase).

### Decisions made

- **Session:** stage 1 pre-survey → stage 2: practice round (no robot), then one round with each
  robot (BAD, GOOD; order counterbalanced), each followed by a post-round survey → stage 3 final
  questions. Design becomes 2 (score mode, between) × 2 (robot, within).
- **Conditions:** from a participant ID typed on the first screen; config can override on our own
  devices.
- **Builds:** one source (`python_build`); scripts generate `html_build` (pygbag) and `exe_build`
  (PyInstaller), each complete and sendable with nothing shared at runtime.
- **Web log:** the browser downloads the `.md` log at the end; no server.
- **Exe:** a PowerShell script Yehen runs on Windows.
- **Rules:** framework plus the three ideas as disabled examples.
- **GOOD robot:** goes for the most urgent falling ball, any colour, at human paddle speed.
- **Sprite:** drawn in code, hot-swappable with PNG images.
- **Speech:** bubbles plus voice files generated with Piper.

### Things to flag (not blocking)

- The report still says three robot levels (worse/matching/better). With two AIs it becomes
  2 × 2; `Report/sections/design.tex` needs updating (not touched by this plan).
- Robot speech and expressions must be identical across all conditions (controlled variable).
- `html_build` can't be opened by double-clicking `index.html` (browsers block it); it needs
  hosting (GitHub Pages or itch.io) before sending links.
- File names use underscores (`pre_questions.py`) because Python can't import hyphenated names.

## Step 1: robot strategies (done, ADR 0006)

- New `src/robot_strategies.py`:
  - `class Strategy(Enum): SWEEP, BAD, GOOD`.
  - One class per strategy with `reset()` and `act(observation) -> action`, tuning values at the
    top of each class.
  - `SWEEP`: today's sweep, kept for testing.
  - `BAD`: random movement. Picks LEFT/RIGHT/STAY at random and holds it for a random
    10–40 frames, so it moves smoothly rather than jittering. It catches balls only by chance.
  - `GOOD`: picks the falling ball (`vy > 0`, in flight) that will reach the paddle row soonest,
    predicts its landing x (including wall bounces), adds an aim error drawn once per target,
    acts on what it saw `reaction_delay_frames` ago, and has a dead zone so it doesn't jitter.
    With no falling ball it drifts back towards its half of the screen.
- `src/robot_agent.py` becomes `class Robot(strategy: Strategy, seed)` with `get_action(observation)`.
  Each robot gets its own seeded RNG, so runs repeat.
- Both robots move at the human's speed: `ROBOT_PADDLE_SPEED = PADDLE_SPEED`, so speed isn't a
  difference between conditions.
- Observation changes to a list of balls (`balls: [{x, y, vx, vy, owner, waiting}]`) so it works
  with any number of balls (step 2 and power-ups).
- `Game(robot_strategy=...)`; `Strategy | None` where `None` means no robot (practice round).
- New `tools/simulate_robot.py`: robot-only headless rounds per strategy; prints catch rate,
  drops and points per minute (numbers for the report).
- Tests: GOOD catches far more than BAD over several seeds; same seed gives the same actions;
  the strategy can be swapped by enum.

## Step 2: colour shows who scores; random respawn (done, ADR 0007)

- `Ball.owner` becomes "who scores next" and the ball is drawn in that colour. It merges with
  `last_hit_by`.
- A paddle hitting a ball takes ownership. If the ball was the other player's, that's a
  **steal** (counted, and a rule hook in step 3).
- A double touch goes to the ball's current owner (keeps the earlier rule).
- Lost ball: `drops[owner] += 1`, then the ball goes to a random player (seeded 50/50; always the
  human when there's no robot) and waits on their paddle.
- Launching: Space launches one waiting human ball per press; the robot's balls auto-launch after
  `ROBOT_RELAUNCH_DELAY_S`. Two balls waiting on one paddle sit side by side.
- The engine holds a plain `balls` list so later rules can add balls.
- `PADDLES_HIT_ANY_BALL` stays `True` (stealing needs it).
- Update ADR 0005 and add ADR `0007-colour-follows-scorer.md`; update tests (credit, steal
  counting, random respawn with seed, double touch).

## Step 3: `rules.py` (done, ADR 0008)

- New `src/rules.py`:
  - A `Rule` base class with no-op hooks: `on_round_start`, `on_tick`,
    `on_brick_broken(ball, brick)`, `on_paddle_hit(paddle, ball)`,
    `on_steal(paddle, ball, from_player)`, `on_ball_lost(ball)`, `on_powerup_caught(paddle, powerup)`.
  - Hooks receive the game and can act through a small, documented engine API:
    `game.add_points(player, n, reason)`, `game.spawn_ball(owner, x, y)`,
    `game.spawn_powerup(kind, x, y)`.
  - `RULES = [LostBallPenalty(enabled=False, points=3), StealBonus(enabled=False, points=2),
    MultiBallPowerUp(enabled=False, drop_chance=0.15)]`: switch a rule on by flipping `enabled`.
  - A header comment shows how to write a new rule in about 5 lines.
- Engine: calls hooks on enabled rules at each event. Adds a generic `PowerUp` entity (falls from
  a broken brick, caught by a paddle, otherwise lost). Its effect is decided by the rule.
- Core rules (row points, colour ownership, random respawn) stay in the engine and config;
  `rules.py` is for optional modifiers.
- Points from rules are tracked by reason, so the log can separate brick points from bonuses
  and penalties.
- Tests: each example rule, when enabled, changes scores or ball count as expected; disabled
  rules do nothing.

## Step 4: Markdown session log (done, ADR 0009)

- New `src/stats.py`: `RoundStats`, fed by engine events. Per player:
  - points: from bricks, and from rules (by reason)
  - bricks broken, paddle hits, steals made, balls stolen from them, balls lost
  - **possession time**: seconds a ball in flight was in their colour (summed over balls)
  - time their balls spent waiting
  - human launch delay (ball waiting → Space)
  - paddle distance moved, time standing still
  - time the two paddles overlapped
  - per round: duration, end reason (timer / bricks cleared / quit), bricks left
- New `src/session_log.py`: writes `logs/<YYYY-MM-DD_HHMMSS>_<pid>.md`.
  - Always a new file: an existing file is never overwritten (a suffix is added if the name is
    taken).
  - Written section by section and flushed, so a crash or early quit keeps everything so far.
  - Marked complete or aborted at the end.
- Log layout:
  - Header: format version, game version, platform (desktop / exe / web), start and end time
  - Participant: ID, score mode, robot order (the independent variables)
  - Settings: config values, enabled rules, robot strategy tuning
  - Stage 1 answers
  - One section per round: a stats table (`Metric | Human | Robot`), then that round's survey
    answers
  - Stage 3 answers
  - Event timeline per round (time, event, player, detail), switchable with `LOG_TIMELINE`
  - A final fenced `json` block with the same data, for analysis scripts
- Desktop and exe write to a `logs/` folder next to the game or exe. Web is handled in step 7.
- Tests: stats for a scripted round; the file is never overwritten; a partial log survives an
  abort.

## Step 5: surveys and the three-stage session (done, ADR 0010)

- New `src/questions.py`, the common interface. Dataclasses, all with
  `id, text, required=True, show_if=None`:
  - `Info` (text and Continue; used for consent and instructions)
  - `MultipleChoice(options, allow_multiple=False)`
  - `Likert(scale=7, low_label, high_label)`
  - `Slider(min, max, step, unit)`
  - `TextAnswer(max_len)`

  `show_if` is a function of the session context (score mode, robot), for questions like
  "shared score players only".
- New `src/pre_questions.py`: `PRE_QUESTIONS`, drafted from the report (placeholders for you to
  edit):
  - consent
  - played Atari/Breakout before
  - how often you play video games
  - taken part in a robot study before
  - age
  - gender (including "prefer not to say")
- New `src/post_questions.py`:
  - `POST_ROUND_QUESTIONS` (after each robot round):
    - teammate / competitor / tool
    - helpfulness (CATME-style)
    - Godspeed likeability (5 items)
    - robot's share of the score (slider)
    - shared-only: "How well did the robot do compared to you?"
    - split-only: "Did seeing the robot's score make you more competitive?"
    - split 10 bonus points
  - `FINAL_QUESTIONS` (stage 3): which robot you preferred and why, and comments.
- New `src/survey_screen.py`: one question per screen, mouse and keyboard, with text input,
  required-answer checks and a progress indicator.
- New `src/assignment.py`:
  - ID → conditions. An optional explicit table, otherwise a formula from the ID's number
    (cycles the 4 cells: shared/split × BAD-first/GOOD-first).
  - `CONDITION_OVERRIDE` in config for our own devices.
- New `src/session.py`: state machine.
  1. ID entry
  2. pre-survey
  3. instructions
  4. practice (no robot, `PRACTICE_SECONDS`, default 60)
  5. for each robot: intro, round, post-round survey
  6. final survey
  7. end screen (log location)

  Pause and quit are handled cleanly; quitting mid-way still saves the log.
- Answers go into the step 4 log. Rerunning makes a new file in `logs/`.
- Tests: assignment covers all 4 cells evenly; `show_if` filtering; a scripted full session
  produces a complete log.

## Step 6: robot persona module (done, ADR 0011)

New package `src/robot_persona/`, the only place persona code lives:

- `persona_config.py`: name, colours, size, talk cooldown, voice on/off, and
  `SPRITE_SOURCE = "auto" | "procedural" | "images"`.
- `sprites.py`:
  - `Expression` enum (neutral, happy, sad, surprised, focused, excited).
  - `ProceduralSprite`: a robot head and body drawn with pygame shapes, with eyes and mouth per
    expression and a blink.
  - `ImageSprite`: loads `assets/robot/<expression>.png`.
  - `"auto"` uses the images when all are present, otherwise draws the procedural robot. This is
    the hot-swap.
- `lines.py`: game event → candidate lines (each with an `id`, text and expression), e.g.
  round start, robot breaks a brick, human breaks one, robot steals, robot loses a ball, human
  loses one, round end.
- `speech.py`: speech bubble above the robot, a queue with a cooldown and priority so it isn't
  spammy, and plays `assets/robot/voice/<id>.ogg` if the file exists.
- `persona.py`: `RobotPersona.on_event(...)`, `update()`, `draw(surface, paddle_x)`. It follows
  the robot paddle so it looks like it's holding it.
- Layout: the screen grows by a strip below the paddle row (`SCREEN_HEIGHT` 600 → about 700);
  balls are lost at the play-area bottom, not the window bottom. The persona is hidden in the
  practice round (no robot).
- `tools/generate_voice.py`: Piper (`piper-tts` dev dependency, voice model downloaded to a
  gitignored cache) turns each line into WAV, then OGG (via `soundfile`) for browser support.
  It only regenerates changed lines. The generated `.ogg` files are committed.
- Spoken lines are logged in the timeline.
- Tests: every line's expression exists; `"auto"` falls back to procedural without images; the
  speech cooldown works; a missing voice file doesn't crash.

## Step 7: restructure and packages

- `git mv Games/Atari_Breakout Atari_Breakout/python_build`; remove `Games/`; update the root
  README and links.
- **`python_build/`**: the source and the "run it with uv" version (`uv run src/main.py`).
- **`build_html.sh`** (Atari_Breakout level):
  - stages `src/` and the assets into a temp folder
  - runs `pygbag --build`
  - copies the result to `Atari_Breakout/html_build/` with a subject README

  In the browser (`sys.platform == "emscripten"`), the end screen triggers a download of the
  `.md` log through `platform.window`. Needs hosting to send as a link.
- **`build_exe.ps1`** (Yehen runs on Windows with uv):
  - copies `python_build` to a Windows temp folder (building from `\\wsl$` is slow and flaky)
  - runs PyInstaller `--onefile --windowed` with the assets bundled
  - outputs `Atari_Breakout/exe_build/HRI_Breakout.exe` and a subject README

  When frozen, logs go next to the exe, and the end screen says which file to send back.
- Generated build contents are gitignored; each build folder keeps a committed `README.md`.
- Update `docs/` (plan, architecture, new ADRs for strategies, rules framework, logging,
  packaging).

## Per-step routine

For each step: implement, add or adjust tests, run `uv run pytest` and `uv run ruff check .` and
`ruff format`, run `tools/simulate_robot.py` or a headless session where relevant, update docs,
then commit. No pushes.

## Verification

- All tests and lint pass after every step.
- Step 1: the simulation shows GOOD clearly outperforming BAD.
- Steps 4–5: a scripted headless session (`--autoplay`, short rounds, scripted answers) writes
  a complete log. Its JSON block parses, a rerun creates a second file, and an aborted run
  leaves a partial log marked aborted.
- Step 6: play by hand and check the sprite, expressions, bubbles and voice. Swap in placeholder
  PNGs to confirm the hot-swap.
- Step 7: `build_html.sh` produces `html_build/`; serve it locally (`python -m http.server`),
  play through in Chrome (devtools MCP) and confirm the log downloads. Yehen runs
  `build_exe.ps1` on Windows and plays the exe once.
- Yehen plays the full desktop session once in each score mode.
