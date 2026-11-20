# HRI Breakout: browser version

This folder holds the browser build, made from `python_build/` by:

    cd ../python_build
    uv run ../build_html.py

The build files (`index.html`, `hri_breakout.apk`, ...) aren't kept in git; build them before
hosting.

## Hosting

Browsers won't run the game from a double-clicked `index.html`; it has to be served over the
web. Upload this folder's build files to any static host, for example:

- **GitHub Pages**: publish this folder from the repo (the build files would then need
  committing).
- **itch.io** (what we use): upload `../html_build_itch.zip`, which the build makes. Project
  settings: kind of project **HTML**; tick **This file will be played in the browser**;
  embed size **800 × 720**; tick **Fullscreen button**; visibility **Restricted** with a
  password. After each rebuild, replace the uploaded zip.

The page loads Python and pygame from pygame-web's CDN, so participants need internet access.
The first load takes 10–30 seconds; then they click the page to start.

## Trying it locally

    python -m http.server --directory html_build 8000

Then open **http://127.0.0.1:8000**. Use 127.0.0.1, not localhost: on "localhost" pygbag
looks for its own development server and fails to load pygame.

## Results

At the end of the session, or if the participant quits with Esc twice, the browser downloads
the results file (`<date>_<time>_<ID>.md`). Participants email it back to us; they can press D
on the end screen to download it again. Closing the tab mid-way loses the results.

## Instructions for participants (for the email)

1. Open the link in Chrome, Edge or Firefox on a computer with a keyboard. Sound on is best.
2. Wait for it to load (up to 30 seconds), then click the page to start.
3. Type the participant ID you were given and follow the instructions (about 15 minutes).
4. At the end your browser downloads a results file named like `2026-11-20_143000_P07.md`.
   **Please email that file back to us.**
