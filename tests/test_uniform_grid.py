from __future__ import annotations

import pygame
import pytest

from game.systems.uniform_grid import UniformGrid


@pytest.fixture
def grid() -> UniformGrid[str]:
    """Create a UniformGrid with standard cell size."""
    return UniformGrid(cell_size=32)


class TestUniformGrid:
    """Tests for Uniform Grid insertion and query operations."""

    def test_insert_and_retrieve(self, grid: UniformGrid[str]) -> None:
        """Insert an item and verify it appears in the correct cell."""
        rect = pygame.Rect(100, 100, 16, 16)
        grid.insert("item", rect)
        results = grid.query(rect)
        assert "item" in results

    def test_query_empty_area(self, grid: UniformGrid[str]) -> None:
        """Query a rect with no items returns empty list."""
        rect = pygame.Rect(0, 0, 10, 10)
        results = grid.query(rect)
        assert len(results) == 0

    def test_item_in_multiple_cells(self, grid: UniformGrid[str]) -> None:
        """A large rect spanning multiple cells is found from any cell."""
        rect = pygame.Rect(0, 0, 64, 64)
        grid.insert("large", rect)
        results = grid.query(pygame.Rect(32, 32, 16, 16))
        assert "large" in results

    def test_clear_all_items(self, grid: UniformGrid[str]) -> None:
        """Clear wipes all items from the grid."""
        grid.insert("a", pygame.Rect(10, 10, 8, 8))
        grid.insert("b", pygame.Rect(20, 20, 8, 8))
        grid.clear()
        results = grid.query(pygame.Rect(0, 0, 640, 480))
        assert len(results) == 0

    def test_query_nearby(self, grid: UniformGrid[str]) -> None:
        """Items in adjacent cells are found by query_nearby."""
        grid.insert("far", pygame.Rect(200, 200, 8, 8))
        results = grid.query_nearby(pygame.Rect(100, 100, 16, 16), radius_cells=4)
        assert "far" in results
