"""The robot's persona: how it looks, what it says, and how it reacts.

Everything about the robot as a character lives in this package, separate from how it plays
(robot_strategies.py):

  persona_config.py  name, colours, size, sprite source, speech and voice settings
  sprites.py         expressions and how the robot is drawn (in code, or from PNG images)
  lines.py           what it says, and when
  speech.py          speech bubbles and voice playback
  persona.py         RobotPersona: listens to game events and ties it all together

The persona behaves the same whatever the robot's strategy or the score mode, so it is not
a difference between conditions.
"""

from robot_persona.persona import RobotPersona
from robot_persona.sprites import Expression

__all__ = ["Expression", "RobotPersona"]
