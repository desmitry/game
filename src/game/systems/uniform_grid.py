from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame import Rect


class UniformGrid:
    """Spatial hashing grid that partitions entities into buckets for fast queries."""

    def __init__(self, cell_size: int) -> None:
        """Initialize grid with a uniform cell size.

        Args:
            cell_size: Width and height of each bucket cell in pixels.
        """
        self.cell_size = cell_size
        self._buckets: dict[tuple[int, int], list[Rect]] = defaultdict(list)

    def _cell_coords(self, x: float, y: float) -> tuple[int, int]:
        """Convert world coordinates to bucket coordinates.

        Args:
            x: World x coordinate.
            y: World y coordinate.

        Returns:
            Tuple of (bucket_x, bucket_y) indices.
        """
        return (int(x // self.cell_size), int(y // self.cell_size))

    def insert(self, rect: Rect) -> None:
        """Add a rectangle to all buckets it overlaps.

        Args:
            rect: Pygame Rect to insert into the grid.
        """
        min_cell = self._cell_coords(rect.left, rect.top)
        max_cell = self._cell_coords(rect.right - 1, rect.bottom - 1)

        for cx in range(min_cell[0], max_cell[0] + 1):
            for cy in range(min_cell[1], max_cell[1] + 1):
                self._buckets[(cx, cy)].append(rect)

    def query(self, rect: Rect) -> list[Rect]:
        """Return all rectangles in buckets overlapping the given rect.

        Args:
            rect: Query rectangle.

        Returns:
            List of rects in overlapping buckets (may contain duplicates).
        """
        min_cell = self._cell_coords(rect.left, rect.top)
        max_cell = self._cell_coords(rect.right - 1, rect.bottom - 1)

        results: list[Rect] = []
        seen: set[int] = set()

        for cx in range(min_cell[0], max_cell[0] + 1):
            for cy in range(min_cell[1], max_cell[1] + 1):
                for item in self._buckets[(cx, cy)]:
                    item_id = id(item)
                    if item_id not in seen:
                        seen.add(item_id)
                        results.append(item)

        return results

    def clear(self) -> None:
        """Remove all entries from the grid."""
        self._buckets.clear()

    def query_nearby(self, rect: Rect, radius_cells: int = 1) -> list[Rect]:
        """Return all rectangles in nearby buckets within a radius.

        Args:
            rect: Center rectangle for the query.
            radius_cells: Number of additional cells to search in each direction.

        Returns:
            List of rects in nearby buckets.
        """
        center = self._cell_coords(rect.centerx, rect.centery)
        results: list[Rect] = []
        seen: set[int] = set()

        for dx in range(-radius_cells, radius_cells + 1):
            for dy in range(-radius_cells, radius_cells + 1):
                bucket = (center[0] + dx, center[1] + dy)
                for item in self._buckets[bucket]:
                    item_id = id(item)
                    if item_id not in seen:
                        seen.add(item_id)
                        results.append(item)

        return results
