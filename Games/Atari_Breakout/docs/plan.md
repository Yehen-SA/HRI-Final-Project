# Build plan: the Breakout study game (web + Python, one codebase)

Status: phase 1 (basic game) built. Phases 2 onwards (settings, session, logging, web) to do.

## Context

The game in `Games/Atari_Breakout/` is a pygame-ce skeleton: config, entities, robot and engine
exist as stubs (`raise NotImplementedError`), and the rules (lives, scoring, round end) are
deferred in `docs/deferred.md`. The playable game comes in two forms that share all
core code:

1. **A website** they can send to subjects as a link. Logs go to an `events` table in a hosted DB.
2. **A Python version** subjects run themselves. Logs go to a file they send back.

Study settings (score shared vs split, robot level poor/average/good, round length, etc.) must
be set from config, not code, and every run must be fully logged: settings, robot and player
scores, each round, and in-game behaviour. The study design is in `Report/sections/design.tex`:
2 (score display, between subjects) × 3 (robot performance, within subjects, counterbalanced),
practice round first, ~3 minute rounds, questionnaire after each round.

Decisions made so far:
- **Web logging:** Supabase (hosted Postgres, insert-only public key).
- **Session:** one launch plays a full session (practice + 3 robot levels) from a participant
  ID and score condition; robot order is counterbalanced from the ID.
- **Robot level:** three fixed presets in config. "Worse/matching/better than the participant"
  is checked afterwards from the logs.
- **Hosting:** decide later. The repo has a GitHub remote, so GitHub Pages is an option; the
  build is static files, so itch.io or any static host also works.

## Phase 1 (built): the most basic playable game

Build this first, desktop only, with no session, study settings, logging or web build yet.
The phases below follow once it plays well. All values live in `src/config.py`.

**Paddles**
- Human: A/D or arrow keys, `PADDLE_SPEED` (7 px/frame). Shared row, paddles pass through
  each other (ADR 0002).
- Robot: no AI. It sweeps left and right across the full screen width, turning at each edge,
  at its own `ROBOT_PADDLE_SPEED` (slower than the human, e.g. 3.5 px/frame). It ignores the
  balls and keeps sweeping while its ball waits on it. This departs from "both paddles follow
  identical movement rules", so `docs/architecture.md` gets updated to say so.

**Balls**
- Two balls, blue (human) and orange (robot). Either paddle bounces either ball
  (`PADDLES_HIT_ANY_BALL = True`). Ball colour stays fixed to its owner.
- Balls pass through each other.
- Constant speed `BALL_START_SPEED`; the per-hit speed-up is turned off.
- Bounce off the top and side walls; falling off the bottom loses the ball.
- Paddle bounce angle depends on where the ball hits (centre = straight up, edges = about 60°
  from vertical).
- If both paddles touch a ball in the same frame, the owner's paddle counts as the hit.

**Launching**
- At game start and after a ball is lost, it waits on its owner's paddle, moving with it.
- Human's ball launches when Space is pressed. Robot's ball launches by itself after
  `ROBOT_RELAUNCH_DELAY_S` = 1 s.
- Launch angle: random 30–60° from vertical, either side, from a seeded RNG (`SEED`) so a run
  can be repeated.
- No lives, no countdown, no paddle freeze. Drops are counted.

**Bricks and scoring**
- A ball breaks one brick per hit and bounces off it.
- Row values from the top: 7, 7, 4, 4, 1, 1 (`BRICK_ROW_POINTS`), Atari style.
- Credit goes to the paddle that last hit the ball. Before any paddle hit (just after launch),
  credit goes to the ball's owner.
- Both scores are always tracked.

**HUD and end**
- `SCORE_MODE` = `"shared"` ("Team: 34") or `"split"` ("You: 20 · Robot: 14 · Total: 34").
  Time left shown on the right.
- The game ends when the timer (`ROUND_SECONDS` = 180) runs out or every brick is gone,
  whichever comes first.
- Game over screen shows the final scores; Space plays again, Esc quits. Esc quits any time.

Phase 1 files: implement `entities.py`, `human_controls.py`, `robot_agent.py` (sweep),
`engine.py`, `main.py`; add the values above to `config.py`; update `docs/deferred.md` (rules
now decided for the basic version, rest still open), `docs/architecture.md`, and add an ADR
`0005-basic-game-rules.md`.

Phase 1 tests (headless, `SDL_VIDEODRIVER=dummy`): brick points by row; credit to last hitter
and to the owner on a same-frame double touch; a lost ball waits on its paddle; the robot's
ball relaunches after 1 s; robot sweep turns at both edges; game ends on timer and on no
bricks; same seed gives the same launch angles; both score modes show the right HUD text.
Then play it by hand.

The settings, presets, session, logging and web sections below become phase 2 onwards, and
the robot presets replace the sweep when that phase starts. Some phase 2 draft values (such as
`paddles_hit_any_ball = false`, `points_per_brick`, countdown respawn) predate the phase 1
rules and should be brought in line with them when phase 2 starts.

## Approach: one Python codebase, browser build with pygbag

[pygbag](https://pygame-web.github.io/) compiles a pygame-ce game to WebAssembly and runs it in
the browser unchanged. So the game logic, the rendering **and** the keyboard input are all
shared. The only things that differ by platform are:

| | Python (desktop) | Website (pygbag) |
|---|---|---|
| Where participant settings come from | `participant.toml` next to the game, overridable by CLI flags | URL query (`?pid=P07&score=shared`) |
| Where events go | JSONL file in `logs/` | Supabase `events` table, via a small JS helper |

`main.py` picks the platform with `sys.platform == "emscripten"`. The main loop is `async`
(`await asyncio.sleep(0)` each frame), which pygbag needs and desktop runs fine with.

Everything else follows the existing Overcooked-style layout (ADR 0003): tuning in config,
robot in `robot_agent.py`, human input in `human_controls.py`, one engine applying actions the
same way to both paddles.

## Settings: three layers

1. **`src/config.py`** (unchanged role): game feel constants (window, sizes, speeds, colours).
2. **`study.toml`** (new, bundled with both builds): everything the study varies or fixes.
3. **Participant layer**: `pid` and `score` (plus optional overrides for piloting) from the
   URL (web) or `participant.toml` / CLI flags (desktop).

A new `src/settings.py` loads and merges these into one frozen `Settings` dataclass, validates
it (unknown keys and bad values are errors, not silently ignored), and the resolved result is
logged in full at session start. Draft `study.toml`:

```toml
[session]
practice_round = true
practice_robot_level = "average"
round_seconds = 180
practice_seconds = 90
robot_levels = ["poor", "average", "good"]
# order: "counterbalanced" (from pid, all 6 orders cycled) or an explicit list
robot_order = "counterbalanced"
pause_between_rounds = true      # "Fill in questionnaire N, then press Space"
questionnaire_urls = []          # optional, shown on the pause screen

[rules]
paddles_hit_any_ball = false
respawn_seconds = 5              # lost ball: countdown on that side, then relaunch
freeze_paddle_while_respawning = true
on_all_bricks_cleared = "reset_bricks"   # round length stays fixed
points_per_brick = 1
seed = 1234                      # same ball launches and layout every round

[robot.poor]
reaction_delay_frames = 14
aim_error_px = 45
miss_chance = 0.25
speed_factor = 0.7
[robot.average]
reaction_delay_frames = 8
aim_error_px = 25
miss_chance = 0.10
speed_factor = 0.85
[robot.good]
reaction_delay_frames = 4
aim_error_px = 10
miss_chance = 0.02
speed_factor = 1.0

[logging]
sample_hz = 10                   # paddle/ball positions; 0 turns sampling off
[logging.web]
supabase_url = ""
supabase_anon_key = ""           # safe to publish: the key can only insert
```

Preset numbers are placeholders; a simulation script (below) tunes them so catch rates are
clearly separated. The rule defaults close the items in `docs/deferred.md` (fixed-length
rounds, no lives, countdown respawn) but stay settings, so they can change without code.

Score mode (`shared` / `split`) only changes the HUD. The engine always tracks each player's
points (credited by whose ball broke the brick), and both are always logged.
- `shared`: "Team: 34"
- `split`: "You: 20 · Robot: 14 · Total: 34"

Counterbalancing: participant number mod 6 picks one of the 6 orders of the 3 levels, so 12
subjects per score condition gives two full sets. The chosen order is logged.

## Logging: one event schema, two sinks

`src/event_log.py` has an `EventLog` with `emit(type, **data)` that stamps every event with
the same envelope, then hands it to a sink. Both sinks write identical rows, so one analysis
loader reads both.

Envelope fields: `session_id` (uuid), `participant_id`, `score_mode`, `platform`
(`web`/`desktop`), `game_version` (from pyproject + git hash at build), `seq`, `t_ms` (since
session start), `round_index`, `round_kind` (`practice`/`main`), `robot_level`, `type`, `data`.

Events:

| type | when | data |
|---|---|---|
| `session_start` | launch | full resolved settings, robot order, seeds, screen size, user agent (web) |
| `round_start` | each round | robot preset values, seed |
| `action_change` | human or robot changes LEFT/RIGHT/STAY | who, action |
| `paddle_hit` | a paddle bounces a ball | paddle, ball owner (other's ball = a rescue), ball speed, hit offset |
| `brick_broken` | brick destroyed | ball owner, row, col, both scores after |
| `ball_lost` | ball falls off screen | owner, x |
| `ball_respawn` | countdown ends | owner |
| `sample` | `sample_hz` times a second | both paddle x, both balls x/y/vx/vy |
| `focus_change` | window/tab loses or regains focus (game pauses) | focused |
| `round_end` | timer runs out | human, robot and team score, drops, hits and rescues per player, bricks broken |
| `session_end` / `session_abort` | finished, or quit early | rounds completed |

**Desktop sink:** `logs/<pid>_<timestamp>_<session_id>.jsonl`, one event per line, flushed
after each write so a crash or early quit keeps everything up to then. The end screen tells the
subject which file to send back.

**Web sink:** a custom pygbag HTML template adds a small JS function `hriLog(json)`. It buffers
events and POSTs them in batches to Supabase's REST API (`/rest/v1/events`) every ~2 s, at
round end, and on `pagehide` using `fetch(..., {keepalive: true})`. Python calls it through
pygbag's `platform.window`. Keeping the network code in JS avoids Python/JS interop quirks.

Supabase table (SQL kept in `supabase/schema.sql`):

```sql
create table events (
  id bigint generated always as identity primary key,
  received_at timestamptz not null default now(),
  session_id uuid not null,
  participant_id text, score_mode text, platform text, game_version text,
  seq int not null, t_ms int not null,
  round_index int, round_kind text, robot_level text,
  type text not null,
  data jsonb not null
);
alter table events enable row level security;
create policy "anyone can insert" on events for insert to anon with check (true);
-- no select policy: the public key can't read anything back
```

**Analysis loader:** `analysis/load_events.py` reads desktop JSONL files and/or a Supabase CSV
export into one pandas DataFrame, plus a per-round summary table from `round_end` events.

## Files

All under `Games/Atari_Breakout/`.

**New**
- `study.toml`: study settings, as above.
- `participant.toml`: per-subject file for the desktop build (`pid`, `score`).
- `src/settings.py`: load, merge, validate settings; counterbalanced order from pid.
- `src/session.py`: session state machine: start screen → practice → pause → round 1 → pause
  → ... → end screen. Owns the round timer and which preset and score mode apply.
- `src/event_log.py`: `EventLog`, `FileSink`, `WebSink` (calls the JS helper), `MemorySink`
  for tests.
- `src/platform_io.py`: reads participant settings and picks the sink for the platform.
- `web/template.tmpl`: pygbag template with the `hriLog` helper.
- `supabase/schema.sql`
- `tools/simulate_robot.py`: runs headless robot-only rounds per preset and prints catch rate
  and points per minute, to tune the presets and report them.
- `tools/make_participant_pack.py`: writes `participant.toml` for a pid and score and zips the
  game for sending; also prints the matching web link.
- `analysis/load_events.py`
- `docs/decisions/0006-web-build-with-pygbag.md`, `0007-event-log-schema-and-sinks.md`,
  `0008-study-settings-layers.md`

**Changed**
- `src/engine.py`: implement the stubs. Keep `update()` free of drawing and pygame display
  calls so it runs headless (tests and simulation). Scoring, respawn countdown and paddle
  freeze go here; emits events through `EventLog`.
- `src/entities.py`, `src/human_controls.py`: implement the stubs.
- `src/robot_agent.py`: `get_robot_action(observation, preset, rng)`; the tuning constants at
  the top become the preset fields read from settings. Seeded RNG so rounds repeat.
- `src/main.py`: async entry point; picks platform; runs the session.
- `src/config.py`: drop the deferred-rules comment once rules move to `study.toml`.
- `docs/architecture.md`, `docs/deferred.md`, `docs/README.md`, `README.md`: update for the
  above, including how to build the web version (`uv run pygbag --build src` →
  `build/web/`) and how to run the desktop version.
- `pyproject.toml`: add `pygbag` and `pandas` to the dev group.
- `.gitignore`: `logs/`, `build/`.

Order of work: settings → entities/engine (headless) → robot presets + simulation → session and
screens → event log + file sink → desktop end to end → web template + Supabase sink → pygbag
build → docs and ADRs.

## Verification

- `uv run pytest` and `uv run ruff check .` pass. New unit tests:
  - settings: merging, validation errors, all 6 counterbalanced orders reached by pid.
  - engine (headless): brick credit goes to the ball's owner; shared and split modes give the
    same underlying scores; ball loss starts the countdown and freezes the paddle; round ends
    on time.
  - robot: same seed gives the same actions.
  - event log: every event has the full envelope; `seq` increases; `MemorySink` sees the
    expected sequence for a scripted short session.
- `tools/simulate_robot.py` shows catch rate poor < average < good with clear gaps.
- e2e: run the desktop game headless (`SDL_VIDEODRIVER=dummy`, `--autoplay --round-seconds 2`)
  through a whole session; check the JSONL file has `session_start`, 4 × `round_start` /
  `round_end`, and `session_end`, and that `load_events.py` reads it.
- Web: `pygbag --build` succeeds; serve `build/web` locally, open
  `?pid=T01&score=split` in Chrome (devtools MCP), play a short session, check the POSTs to
  Supabase return 201 and the rows appear in the table; check that the anon key can't select.
- Play both versions by hand once to check the HUD in each score mode and the pause screens.
