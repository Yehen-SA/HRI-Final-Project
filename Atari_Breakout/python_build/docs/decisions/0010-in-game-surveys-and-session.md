# 0010: Surveys run inside the game, as a three-stage session

Status: accepted

## Context

Running questionnaires separately (paper or online forms) means matching answers to game logs
by hand, and subjects playing on their own computers would need extra links. We want one
program that takes a participant from consent to the last question, with everything in one log.

## Decision

- A session is: participant ID → stage 1 (pre-game questions, instructions) → stage 2
  (practice round without the robot, then a round with each robot, each followed by
  post-round questions) → stage 3 (final questions) → end screen.
- The robot design becomes within-subjects with two robots (BAD and GOOD); the order is
  counterbalanced.
- Conditions come from the participant ID (`assignment.py`): consecutive IDs cycle through the
  four combinations of score mode and robot order. `MANUAL_ASSIGNMENTS` and `CONDITION_OVERRIDE`
  allow manual assignment.
- Questions are data: `pre_questions.py` and `post_questions.py` hold lists of question objects
  from `questions.py` (`Info`, `Consent`, `MultipleChoice`, `Likert`, `Slider`, `TextAnswer`),
  each with an `id`, `required` and an optional `show_if` (e.g. shared-score only).
  `{robot_name}` in the text is filled in.
- Answers go into the session log as they're given. Declining consent ends the session with the
  log marked "declined".
- Sliders count as answered only once moved, so a lazy default isn't recorded as an answer.
- `Session.flow()` is a generator that yields one screen at a time, so the order of the session
  reads top to bottom in one method.
- Esc pauses; Esc again quits, keeping a partial log marked "aborted".

## Consequences

- One file per participant holds conditions, answers and game data together.
- The question wording in the files is a draft and must be checked against the final
  questionnaire in the report.
- `--autoplay`, `--pid` and `--round-seconds` let tests (and us) run a whole session quickly.
