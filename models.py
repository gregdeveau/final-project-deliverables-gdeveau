# models.py
# This file contains the main object-oriented game models for the stealth maze game.

import random
import tkinter as tk

from loader import load_all_levels
from scoreboard import ScoreBoard
from util import (
    CELL_SIZE,
    ENEMY_COLOR,
    ENEMY_STEP_MS,
    FLOOR_COLOR,
    HUD_HEIGHT,
    INTEL_COLOR,
    PLAYER_COLOR,
    ROUND_COMPLETE_MS,
    ROUND_START_SECONDS,
    SCORES_FILE,
    STEP_MS,
    TEXT_COLOR,
    WALL_COLOR,
)


class Entity:
    def __init__(self, row: int, col: int, color: str):
        self.row = row
        self.col = col
        self.start_row = row
        self.start_col = col
        self.color = color

    def reset(self):
        self.row = self.start_row
        self.col = self.start_col


class Player(Entity):
    def __init__(self, row: int, col: int):
        super().__init__(row, col, PLAYER_COLOR)
        self.score = 0
        self.lives = 3
        self.has_intel = False


class Enemy(Entity):
    def __init__(self, row: int, col: int):
        super().__init__(row, col, ENEMY_COLOR)
        self.previous_cell = (row, col)

    def reset(self):
        super().reset()
        self.previous_cell = (self.row, self.col)


class Level:
    WALL = "#"
    FLOOR = "."
    EMPTY = " "
    PLAYER = "P"
    ENEMY = "E"
    INTEL = "I"

    def __init__(self, level_map):
        self.original = [list(row) for row in level_map]
        self.height = len(self.original)
        self.width = len(self.original[0]) if self.original else 0
        self.grid = []
        self.player_start = (1, 1)
        self.enemy_starts = []
        self.intel_start = (1, 1)
        self.intel_found = False
        self.reset()

    def reset(self):
        self.grid = [row[:] for row in self.original]
        self.enemy_starts = []
        self.intel_found = False
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell == self.PLAYER:
                    self.player_start = (r, c)
                    self.grid[r][c] = self.FLOOR
                elif cell == self.ENEMY:
                    self.enemy_starts.append((r, c))
                    self.grid[r][c] = self.FLOOR
                elif cell == self.INTEL:
                    self.intel_start = (r, c)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def is_wall(self, row: int, col: int) -> bool:
        return self.grid[row][col] == self.WALL

    def is_walkable(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and not self.is_wall(row, col)

    def collect_intel_at(self, row: int, col: int) -> bool:
        if self.grid[row][col] == self.INTEL:
            self.grid[row][col] = self.FLOOR
            self.intel_found = True
            return True
        return False


class Game:
    DIRECTIONS = {
        "Up": (-1, 0),
        "Down": (1, 0),
        "Left": (0, -1),
        "Right": (0, 1),
        "w": (-1, 0),
        "s": (1, 0),
        "a": (0, -1),
        "d": (0, 1),
        "W": (-1, 0),
        "S": (1, 0),
        "A": (0, -1),
        "D": (0, 1),
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Stealth Maze Game")
        self.level_maps = load_all_levels()
        if not self.level_maps:
            raise ValueError("No level files were loaded.")

        self.scoreboard = ScoreBoard(SCORES_FILE)
        self.level_index = 0
        self.level = None
        self.player = None
        self.enemies = []
        self.game_over = False
        self.win = False
        self.default_message = "Find the intel and avoid the guards. Arrow keys or WASD to move."
        self.message = self.default_message
        self.pending_move = None
        self.enemy_loop_id = None
        self.player_loop_id = None
        self.countdown_loop_id = None
        self.round_complete_loop_id = None
        self.round_countdown = 0
        self.round_ready_message = self.default_message
        self.show_round_complete = False
        self.pending_level_index = None

        self.load_level(reset_progress=True)

        width = self.level.width * CELL_SIZE
        height = self.level.height * CELL_SIZE + HUD_HEIGHT
        self.canvas = tk.Canvas(root, width=width, height=height, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.root.bind("<KeyPress>", self.handle_keypress)
        self.restart_button = tk.Button(root, text="Restart Game", command=self.restart_game)
        self.restart_button.pack(pady=6)

        self.begin_round(self.default_message)

    def load_level(self, reset_progress: bool):
        score = 0
        lives = 3
        if not reset_progress and self.player is not None:
            score = self.player.score
            lives = self.player.lives

        self.level = Level(self.level_maps[self.level_index])
        self.player = Player(*self.level.player_start)
        self.player.score = score
        self.player.lives = lives
        self.player.has_intel = False
        self.enemies = [Enemy(r, c) for r, c in self.level.enemy_starts]

        if hasattr(self, "canvas"):
            width = self.level.width * CELL_SIZE
            height = self.level.height * CELL_SIZE + HUD_HEIGHT
            self.canvas.config(width=width, height=height)

    def start_loops(self):
        self.stop_loops()
        self.player_loop_id = self.root.after(STEP_MS, self.game_tick)
        self.enemy_loop_id = self.root.after(ENEMY_STEP_MS, self.enemy_tick)

    def stop_loops(self):
        if self.player_loop_id is not None:
            self.root.after_cancel(self.player_loop_id)
            self.player_loop_id = None
        if self.enemy_loop_id is not None:
            self.root.after_cancel(self.enemy_loop_id)
            self.enemy_loop_id = None
        if self.countdown_loop_id is not None:
            self.root.after_cancel(self.countdown_loop_id)
            self.countdown_loop_id = None
        if self.round_complete_loop_id is not None:
            self.root.after_cancel(self.round_complete_loop_id)
            self.round_complete_loop_id = None

    def begin_round(self, ready_message: str):
        self.stop_loops()
        self.pending_move = None
        self.show_round_complete = False
        self.round_ready_message = ready_message
        self.round_countdown = ROUND_START_SECONDS
        self.message = f"Round starts in {self.round_countdown}"
        self.draw()
        self.countdown_loop_id = self.root.after(1000, self.countdown_tick)

    def countdown_tick(self):
        self.countdown_loop_id = None
        if self.game_over:
            return

        self.round_countdown -= 1
        if self.round_countdown > 0:
            self.message = f"Round starts in {self.round_countdown}"
            self.draw()
            self.countdown_loop_id = self.root.after(1000, self.countdown_tick)
            return

        self.round_countdown = 0
        self.message = self.round_ready_message
        self.start_loops()
        self.draw()

    def restart_game(self):
        self.level_index = 0
        self.game_over = False
        self.win = False
        self.pending_move = None
        self.load_level(reset_progress=True)
        self.begin_round(self.default_message)

    def next_level(self):
        next_level_index = self.level_index + 1
        if next_level_index >= len(self.level_maps):
            self.win = True
            self.game_over = True
            self.message = "Mission complete. You escaped with the intel."
            self.finish_game()
            return

        self.show_round_complete_screen(next_level_index)

    def show_round_complete_screen(self, next_level_index: int):
        self.stop_loops()
        self.pending_move = None
        self.round_countdown = 0
        self.show_round_complete = True
        self.pending_level_index = next_level_index
        self.message = "Round complete."
        self.draw()
        self.round_complete_loop_id = self.root.after(ROUND_COMPLETE_MS, self.load_next_round)

    def load_next_round(self):
        self.round_complete_loop_id = None
        if self.pending_level_index is None:
            return

        self.show_round_complete = False
        self.level_index = self.pending_level_index
        self.pending_level_index = None
        self.load_level(reset_progress=False)
        self.begin_round(f"Level {self.level_index + 1}. Find the intel.")

    def finish_game(self):
        self.stop_loops()
        self.scoreboard.save_result(self.player.score)

    def handle_keypress(self, event):
        if self.round_countdown > 0 or self.show_round_complete:
            return
        if event.keysym in self.DIRECTIONS:
            self.pending_move = self.DIRECTIONS[event.keysym]

    def game_tick(self):
        if not self.game_over and self.pending_move:
            self.move_player(*self.pending_move)
        self.draw()
        if not self.game_over:
            self.player_loop_id = self.root.after(STEP_MS, self.game_tick)

    def enemy_tick(self):
        if not self.game_over:
            for enemy in self.enemies:
                self.move_enemy(enemy)
            self.check_collisions()
            self.draw()
            self.enemy_loop_id = self.root.after(ENEMY_STEP_MS, self.enemy_tick)

    def move_player(self, dr: int, dc: int):
        nr = self.player.row + dr
        nc = self.player.col + dc
        if not self.level.is_walkable(nr, nc):
            self.message = "Wall hit. Choose another direction."
            return

        self.player.row = nr
        self.player.col = nc
        self.check_collisions()
        if self.game_over:
            return

        if self.check_intel_pickup():
            return

        self.message = "Sneaking through the maze."

    def move_enemy(self, enemy: Enemy):
        neighbors = self.valid_neighbors(enemy.row, enemy.col)
        if not neighbors:
            return

        choices = neighbors
        if len(neighbors) > 1 and enemy.previous_cell in neighbors:
            choices = [cell for cell in neighbors if cell != enemy.previous_cell]

        target = random.choice(choices)
        enemy.previous_cell = (enemy.row, enemy.col)
        enemy.row, enemy.col = target

    def valid_neighbors(self, row: int, col: int):
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr = row + dr
            nc = col + dc
            if self.level.is_walkable(nr, nc):
                moves.append((nr, nc))
        return moves

    def check_collisions(self):
        for enemy in self.enemies:
            if enemy.row == self.player.row and enemy.col == self.player.col:
                self.player.lives -= 1
                if self.player.lives <= 0:
                    self.game_over = True
                    self.message = "Mission failed. Press Restart Game to try again."
                    self.finish_game()
                else:
                    self.reset_positions()
                    self.begin_round("Back to the start. Avoid the guards.")
                break

    def reset_positions(self):
        self.player.reset()
        self.player.has_intel = False
        for enemy in self.enemies:
            enemy.reset()

    def check_intel_pickup(self) -> bool:
        if self.level.collect_intel_at(self.player.row, self.player.col):
            self.player.has_intel = True
            self.player.score += 100
            self.message = "Intel secured. Warping out."
            self.warp_to_exit()
            return True
        return False

    def warp_to_exit(self):
        self.player.score += 150
        self.next_level()

    def draw(self):
        self.canvas.delete("all")
        self.draw_hud()
        self.draw_board()
        self.draw_entities()
        if self.game_over:
            self.draw_overlay()
        elif self.show_round_complete:
            self.draw_round_complete_overlay()
        elif self.round_countdown > 0:
            self.draw_countdown_overlay()

    def draw_hud(self):
        width = self.level.width * CELL_SIZE
        self.canvas.create_rectangle(0, 0, width, HUD_HEIGHT, fill="#111", outline="#333")
        intel_state = "Secured" if self.player.has_intel else "Searching"
        hud_text = (
            f"Level: {self.level_index + 1}    "
            f"Score: {self.player.score}    "
            f"Best: {self.scoreboard.best_score}    "
            f"Lives: {self.player.lives}    "
            f"Intel: {intel_state}"
        )
        self.canvas.create_text(
            12,
            18,
            anchor="w",
            text=hud_text,
            fill=TEXT_COLOR,
            font=("Consolas", 14, "bold"),
        )
        self.canvas.create_text(
            12,
            42,
            anchor="w",
            text=self.message,
            fill="#ddd",
            font=("Consolas", 10),
        )

    def draw_board(self):
        for r in range(self.level.height):
            for c in range(self.level.width):
                x1 = c * CELL_SIZE
                y1 = HUD_HEIGHT + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                cell = self.level.grid[r][c]
                fill = WALL_COLOR if cell == Level.WALL else FLOOR_COLOR
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#222")
                if cell == Level.INTEL:
                    self.canvas.create_rectangle(
                        x1 + 8,
                        y1 + 8,
                        x2 - 8,
                        y2 - 8,
                        fill=INTEL_COLOR,
                        outline=INTEL_COLOR,
                    )

    def draw_entities(self):
        self.draw_entity(self.player, 5, 5, self.player.color)
        for enemy in self.enemies:
            self.draw_entity(enemy, 6, 6, enemy.color)

    def draw_entity(self, entity: Entity, pad_x: int, pad_y: int, color: str):
        x1 = entity.col * CELL_SIZE + pad_x
        y1 = HUD_HEIGHT + entity.row * CELL_SIZE + pad_y
        x2 = (entity.col + 1) * CELL_SIZE - pad_x
        y2 = HUD_HEIGHT + (entity.row + 1) * CELL_SIZE - pad_y
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="")

    def draw_countdown_overlay(self):
        width = self.level.width * CELL_SIZE
        board_height = self.level.height * CELL_SIZE
        center_y = HUD_HEIGHT + (board_height / 2)
        self.canvas.create_rectangle(0, HUD_HEIGHT, width, HUD_HEIGHT + board_height, fill="black", stipple="gray50")
        self.canvas.create_text(
            width / 2,
            center_y - 25,
            text="ROUND STARTS IN",
            fill="white",
            font=("Consolas", 18, "bold"),
        )
        self.canvas.create_text(
            width / 2,
            center_y + 20,
            text=str(self.round_countdown),
            fill="white",
            font=("Consolas", 34, "bold"),
        )

    def draw_round_complete_overlay(self):
        width = self.level.width * CELL_SIZE
        board_height = self.level.height * CELL_SIZE
        center_y = HUD_HEIGHT + (board_height / 2)
        self.canvas.create_rectangle(0, HUD_HEIGHT, width, HUD_HEIGHT + board_height, fill="black", stipple="gray50")
        self.canvas.create_text(
            width / 2,
            center_y - 10,
            text="ROUND COMPLETE",
            fill="white",
            font=("Consolas", 24, "bold"),
        )
        self.canvas.create_text(
            width / 2,
            center_y + 28,
            text="Loading next round...",
            fill="white",
            font=("Consolas", 12),
        )

    def draw_overlay(self):
        width = self.level.width * CELL_SIZE
        height = self.level.height * CELL_SIZE + HUD_HEIGHT
        self.canvas.create_rectangle(0, 0, width, height, fill="black", stipple="gray50")
        title = "MISSION COMPLETE" if self.win else "MISSION FAILED"
        self.canvas.create_text(
            width / 2,
            height / 2 - 20,
            text=title,
            fill="white",
            font=("Consolas", 26, "bold"),
        )
        self.canvas.create_text(
            width / 2,
            height / 2 + 18,
            text=f"Final Score: {self.player.score}   Best Score: {max(self.scoreboard.best_score, self.player.score)}",
            fill="white",
            font=("Consolas", 12),
        )
        self.canvas.create_text(
            width / 2,
            height / 2 + 48,
            text="Press Restart Game to play again.",
            fill="white",
            font=("Consolas", 12),
        )


def main():
    root = tk.Tk()
    Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
