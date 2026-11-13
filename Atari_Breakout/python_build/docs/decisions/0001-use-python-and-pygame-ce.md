# 0001: Use Python and pygame-ce

Status: accepted

## Context

The user study needs a simple, controllable Breakout game that can log player actions and
later connect to the robot side of the project.

## Decision

Write the game in Python with pygame-ce, managed with uv.

## Consequences

- Same language as most robotics and data-analysis tooling, so study logs and robot
  integration stay in one ecosystem.
- pygame-ce is a maintained fork of pygame with current Python wheels.
