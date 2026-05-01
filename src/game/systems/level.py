from __future__ import annotations

from typing import TYPE_CHECKING

from game.ai.pathfinding_grid import PathfindingGrid
from game.systems.uniform_grid import UniformGrid

if TYPE_CHECKING:
    from pygame import Rect

    from game.models.wall import Wall

CELL_SIZE = 64


class Level:
    """Manages static map geometry and spatial indexing."""

    def __init__(self, width: int, height: int) -> None:
        """Initialize level with grid boundaries.

        Args:
            width: Level width in pixels.
            height: Level height in pixels.
        """
        self.width = width
        self.height = height
        self.grid: UniformGrid[Wall] = UniformGrid(CELL_SIZE)
        self.walls: list[Wall] = []
        self._pf_grid = PathfindingGrid(width // 32, height // 32)

    @property
    def pathfinding_grid(self) -> PathfindingGrid:
        """Return the pathfinding grid, rebuilding if needed."""
        wall_rects = [w.rect for w in self.walls]
        self._pf_grid.clear_obstacles()
        self._pf_grid.add_obstacles_from_rects(wall_rects, self.width, self.height)
        return self._pf_grid

    def add_wall(self, wall: Wall) -> None:
        """Register a wall and insert it into the spatial grid.

        Args:
            wall: Wall to add to the level.
        """
        self.walls.append(wall)
        self.grid.insert(wall, wall.rect)

    def rebuild_grid(self) -> None:
        """Rebuild the spatial grid from all registered walls."""
        self.grid.clear()
        for wall in self.walls:
            self.grid.insert(wall, wall.rect)

    def get_nearby_walls(self, rect: Rect) -> list[Wall]:
        """Query walls near the given rectangle using the spatial grid.

        Args:
            rect: Query rectangle.

        Returns:
            List of Wall objects in nearby buckets.
        """
        return self.grid.query_nearby(rect)
