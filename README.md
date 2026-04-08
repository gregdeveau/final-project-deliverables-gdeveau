# Stealth Maze Game

This repository contains my PROG1400 stealth maze game project.
The player moves through a maze, avoids enemies, collects the intel piece, and warps out to win.

## Project Structure

- `models.py` - main game classes
- `loader.py` - level loading helpers
- `util.py` - shared utility classes and enums
- `highscore.txt` - stored high score
- `levels/level1.txt` - level 1 layout
- `levels/level2.txt` - level 2 layout

## Current Game Idea

- The game is a stealth maze inspired by Pac-Man.
- Enemies move around the maze but do not chase the player.
- There are no pellets to collect.
- The main objective is to collect the intel piece.
- When the player picks up the intel, they warp out and win the level.

## Map Symbols

- `#` = wall
- `.` = open floor
- `P` = player start
- `E` = enemy start
- `I` = intel piece
