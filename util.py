# util.py
# This file contains shared utility classes, enums, and helper structures used by the game.

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Cell:
    row: int
    col: int


class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    NONE = "NONE"
