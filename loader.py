# loader.py
# This file is responsible for loading and interpreting level data from text files.

from pathlib import Path


LEVEL_CHARS = set("#.PEI ")
LEVELS_DIR = Path(__file__).with_name("levels")


def load_level_from_ascii(path):
    rows = []
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip("\n")
        if line and set(line).issubset(LEVEL_CHARS):
            rows.append(line)
    return rows


def load_all_levels():
    levels = []
    for filename in ["level1.txt", "level2.txt"]:
        level_path = LEVELS_DIR / filename
        if level_path.exists():
            level_rows = load_level_from_ascii(level_path)
            if level_rows:
                levels.append(level_rows)
    return levels
