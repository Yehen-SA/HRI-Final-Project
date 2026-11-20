# Study data

## participant_logs/

Put every participant's log file here: the `.md` file the game writes (`logs/` next to the
game or the .exe, or the browser's download). One file per session, named
`<date>_<time>_<participant ID>.md`. Don't rename or edit them. This folder is committed to git,
so everyone's logs end up in one place.

Logs hold participant data, keyed by participant ID only. Don't add files with names or
contact details.

## Summarising

From `Atari_Breakout/python_build/`:

    uv run tools/summarise_logs.py

This reads every log in `participant_logs/` and:

- prints, per participant, the values for the report's data table (Appendix B): possession,
  steals and rescues as unsimplified fractions, and scores, ready to copy into Overleaf;
- writes `results.csv` here: one row per participant per robot round with every measure the
  game records (all stats for both players, the round's questionnaire answers, and the
  pre-game answers). Use this file for the analysis.

The interviewer and the "Started" tick are filled in by hand in the Overleaf table.
