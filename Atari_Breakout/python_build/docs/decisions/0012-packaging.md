# 0012: One source, packaged for the browser and as a Windows .exe

Status: accepted

## Context

Some subjects play on our devices; others play on their own and send their results back. We
considered sending a Windows .exe and porting the game to HTML. Writing the game twice (Python
and JavaScript) would mean every change made twice.

## Decision

- Layout: `Atari_Breakout/python_build/` (the only source), `Atari_Breakout/html_build/` and
  `Atari_Breakout/exe_build/` (generated, each a complete package with nothing shared at
  runtime).
- Browser: pygbag runs the same Python game in the browser (WebAssembly). `build_html.py`
  copies `src/` and `assets/` into `.html_stage/hri_breakout/` and runs pygbag. The session log
  is downloaded at the end (and on quitting with Esc twice); D on the end screen downloads it
  again. No server is involved.
- Windows: `build_exe.ps1`, run on Windows, makes a one-file windowed exe with PyInstaller.
  Logs go to `logs/` next to the exe; the end screen shows the path.
- Code rules for the browser build, found while testing it:
  - `main.py` imports pygame directly, so pygbag loads it.
  - `main.py` ends in a plain `asyncio.run(...)`; a `SystemExit` stops pygbag early.
  - No `statistics` module (pygbag's Python lacks it and tries to install an unrelated PyPI
    package instead).
  - Assets are found relative to the module (`paths.py`), which works from source, from
    PyInstaller (`sys._MEIPASS`) and in the browser.
- Build outputs are gitignored; each output folder keeps a README with hosting or participant
  instructions.

## Consequences

- One codebase; rebuild both packages after any change.
- The browser version needs hosting (GitHub Pages or itch.io) and internet access: it loads
  Python and pygame from pygame-web's CDN. When testing locally, use 127.0.0.1, not localhost.
- Browser subjects who close the tab mid-way lose their results. Exe subjects keep a partial
  log.
- The exe is unsigned, so Windows SmartScreen warns; the participant instructions explain
  "More info → Run anyway".
- Tested: the browser build in headless Chromium (ID entry, surveys, practice, a robot round
  with persona, quit → log downloaded). The exe build hasn't been run yet (needs Windows).
