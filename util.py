# util.py
# This file contains shared utility values used by the game.

from pathlib import Path


CELL_SIZE = 28
HUD_HEIGHT = 60
STEP_MS = 140
ENEMY_STEP_MS = 240
PLAYER_COLOR = "gold"
ENEMY_COLOR = "tomato"
WALL_COLOR = "navy"
FLOOR_COLOR = "black"
INTEL_COLOR = "cyan"
TEXT_COLOR = "white"

SCORES_FILE = Path(__file__).with_name("highscore.txt")
