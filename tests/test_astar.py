from __future__ import annotations

import pytest

from ai.astar import astar
from ai.pathfinding_grid import PathfindingGrid


@pytest.fixture
def empty_grid() -> PathfindingGrid:
    """Create a small grid with no obstacles."""
    grid = PathfindingGrid(width=320, height=240)
    return grid


@pytest.fixture
def blocked_grid() -> PathfindingGrid:
    """Create a grid with a wall of blocked tiles."""
    grid = PathfindingGrid(width=320, height=240)
    for y in range(5, 10):
        grid.set_blocked(10, y, blocked=True)
    return grid


class TestAStar:
    """Tests for A* pathfinding validity."""

    def test_adjacent_tiles(self, empty_grid: PathfindingGrid) -> None:
        """Path between adjacent tiles is immediate."""
        path = astar(empty_grid, (5, 5), (6, 5))
        assert len(path) >= 2
        assert path[0] == (5, 5)
        assert path[-1] == (6, 5)

    def test_same_start_and_goal(self, empty_grid: PathfindingGrid) -> None:
        """Path from a tile to itself returns single element."""
        path = astar(empty_grid, (3, 3), (3, 3))
        assert path == [(3, 3)]

    def test_unreachable_goal(self, empty_grid: PathfindingGrid) -> None:
        """Returns empty path when goal tile is blocked."""
        empty_grid.set_blocked(5, 5, blocked=True)
        path = astar(empty_grid, (5, 5), (6, 5))
        assert len(path) == 0

    def test_path_avoids_obstacles(self, blocked_grid: PathfindingGrid) -> None:
        """Path goes around blocked tiles rather than through them."""
        path = astar(blocked_grid, (5, 7), (15, 7))
        assert len(path) > 0
        for tx, ty in path:
            assert not blocked_grid.is_blocked(tx, ty), (
                f"Path goes through blocked tile ({tx}, {ty})"
            )

    def test_path_starts_and_ends_correctly(self, empty_grid: PathfindingGrid) -> None:
        """Path starts at start and ends at goal."""
        path = astar(empty_grid, (2, 3), (8, 7))
        assert path[0] == (2, 3)
        assert path[-1] == (8, 7)

    def test_out_of_bounds_goal(self, empty_grid: PathfindingGrid) -> None:
        """Goal outside grid returns empty path."""
        path = astar(empty_grid, (5, 5), (999, 999))
        assert len(path) == 0
