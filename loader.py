# loader.py
# This file is responsible for loading and interpreting level data from text files.


def load_level_from_ascii(path):
    """Read a level file and return its lines as a list of strings."""
    with open(path, "r", encoding="utf-8") as level_file:
        return [line.rstrip("\n") for line in level_file]
