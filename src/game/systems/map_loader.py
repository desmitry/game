from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from game.models.wall import Wall

if TYPE_CHECKING:
    from game.systems.level import Level

TILE_SIZE = 32
WALL_CHAR = "#"


def load_map(filepath: str, level: Level) -> None:
    """Parse a text-based map file and populate the level with walls.

    Args:
        filepath: Path to the map text file.
        level: Level instance to populate.
    """
    path = Path(filepath)
    if not path.exists():
        return

    with path.open(encoding="utf-8") as f:
        lines = f.readlines()

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == WALL_CHAR:
                wall = Wall(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                level.add_wall(wall)
