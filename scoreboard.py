from pathlib import Path


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
