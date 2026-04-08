# models.py
# This file contains the main object-oriented game models for the stealth maze game.

from dataclasses import dataclass, field

from util import Cell, Direction


@dataclass
class Actor:
    """Base class for anything that can move in the maze."""

    position: Cell
    direction: Direction = Direction.NONE


@dataclass
class Player(Actor):
    """The player tries to reach the intel without touching enemies."""

    has_intel: bool = False


@dataclass
class Enemy(Actor):
    """An enemy patrols the maze without directly chasing the player."""

    patrol_mode: str = "random"


@dataclass
class Intel:
    """The intel piece is the main objective item."""

    position: Cell
    collected: bool = False


@dataclass
class Maze:
    """Stores the maze layout and important positions."""

    rows: list[str] = field(default_factory=list)
    player_start: Cell = field(default_factory=lambda: Cell(0, 0))
    enemy_starts: list[Cell] = field(default_factory=list)
    intel_start: Cell = field(default_factory=lambda: Cell(0, 0))


class Game:
    """Coordinates the maze, player, enemies, and win or lose conditions."""

    def __init__(self):
        self.maze = Maze()
        self.player = Player(Cell(0, 0))
        self.enemies: list[Enemy] = []
        self.intel = Intel(Cell(0, 0))
        self.has_won = False
        self.is_game_over = False

    def move_player(self, direction: Direction):
        """Move the player one step if the next tile is valid."""
        self.player.direction = direction

    def move_enemies(self):
        """Move enemies using simple non-chasing behavior."""
        pass

    def check_enemy_collision(self):
        """End the game if an enemy reaches the player."""
        pass

    def check_intel_pickup(self):
        """Mark the intel as collected and trigger the win state."""
        pass

    def warp_to_exit(self):
        """Handle the warp-out win sequence after the intel is collected."""
        pass
