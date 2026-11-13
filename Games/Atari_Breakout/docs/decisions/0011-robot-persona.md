# 0011: The robot has a persona: sprite, expressions, speech and voice

Status: accepted

## Context

A paddle that moves by itself reads as an NPC, not an agent. For subjects to judge the robot as
a teammate (or competitor), it needs to look like someone is there: a body, a face that reacts,
and a voice.

## Decision

- A separate package, `robot_persona/`, holds everything about the robot as a character, apart
  from how it plays (`robot_strategies.py`).
- The window grows to 720 px. Below the play area (`PLAY_BOTTOM` = 600) the robot sits under
  its paddle, holding it up with two arms, and follows it.
- Six expressions (neutral, happy, sad, surprised, focused, excited), plus blinking. The
  robot is drawn in code by default. With `SPRITE_SOURCE = "auto"`, a full set of PNGs in
  `assets/robot/` replaces it with no code change.
- It reacts to game events (bricks, steals, lost balls, round start and end), with a short
  expression and sometimes a line, chosen at random from `lines.py`. A cooldown and priorities
  keep it from talking too much; it says an idle line after 25 s of quiet.
- Speech bubbles sit beside the robot in its strip, never over the play area.
- Voice: `tools/generate_voice.py` makes one OGG per line with Piper (voice
  `en_GB-alan-medium`). Files are named by a hash of the text, so only new or changed lines are
  generated. The game plays a line's file if it exists and stays silent otherwise.
- The persona behaves the same for both strategies and both score modes. The GOOD robot still
  triggers more happy reactions, because it catches more.
- Spoken lines are logged in the timeline (`robot_said`).

## Consequences

- The robot's speech is friendly and team-flavoured ("Good shot!", "Nice catch!"). That's the
  same for every condition, but it may push all subjects towards seeing it as a teammate. The
  lines should be reviewed with that in mind.
- Editing a line needs the voice files regenerated; a test fails if any line has no voice file.
- `piper-tts` and `soundfile` are dev dependencies only; the game just plays the OGG files.
