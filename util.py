# util.py
# This file contains shared utility values and score helpers used by the game.

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


class ScoreBoard:
    def __init__(self, path: Path):
        self.path = path
        self.best_score = 0
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                value = self.path.read_text(encoding="utf-8").strip()
                self.best_score = int(value or "0")
            except Exception:
                self.best_score = 0

    def save_result(self, score: int):
        self.best_score = max(self.best_score, score)
        self.path.write_text(str(self.best_score), encoding="utf-8")
