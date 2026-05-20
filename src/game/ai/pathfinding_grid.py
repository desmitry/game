TILE_SIZE = 32


class PathfindingGrid:
    """Grid-based navigation map for A* pathfinding."""

    def __init__(self, width: int, height: int) -> None:
        """Initialize grid with dimensions in tiles.

        Args:
            width: Number of columns.
            height: Number of rows.
        """
        self.width = width
        self.height = height
        self.obstacles: set[tuple[int, int]] = set()

    def world_to_tile(self, x: float, y: float) -> tuple[int, int]:
        """Convert world coordinates to tile coordinates.

        Args:
            x: World x coordinate.
            y: World y coordinate.

        Returns:
            Tuple of (tile_x, tile_y).
        """
        return (int(x // TILE_SIZE), int(y // TILE_SIZE))

    def tile_to_world(self, tile_x: int, tile_y: int) -> tuple[float, float]:
        """Convert tile coordinates to world center coordinates.

        Args:
            tile_x: Tile column index.
            tile_y: Tile row index.

        Returns:
            Tuple of (world_x, world_y) at tile center.
        """
        return (
            tile_x * TILE_SIZE + TILE_SIZE / 2,
            tile_y * TILE_SIZE + TILE_SIZE / 2,
        )

    def is_valid(self, tile_x: int, tile_y: int) -> bool:
        """Check if a tile is within bounds and not an obstacle.

        Args:
            tile_x: Tile column index.
            tile_y: Tile row index.

        Returns:
            True if the tile is walkable.
        """
        if tile_x < 0 or tile_x >= self.width:
            return False
        if tile_y < 0 or tile_y >= self.height:
            return False
        return (tile_x, tile_y) not in self.obstacles

    def is_blocked(self, tile_x: int, tile_y: int) -> bool:
        """Check if a tile is blocked.

        Args:
            tile_x: Tile column index.
            tile_y: Tile row index.

        Returns:
            True if the tile is an obstacle.
        """
        return (tile_x, tile_y) in self.obstacles

    def set_blocked(self, tile_x: int, tile_y: int, *, blocked: bool = True) -> None:
        """Mark or unmark a tile as blocked.

        Args:
            tile_x: Tile column index.
            tile_y: Tile row index.
            blocked: Whether the tile should be blocked.
        """
        if blocked:
            self.obstacles.add((tile_x, tile_y))
        else:
            self.obstacles.discard((tile_x, tile_y))

    def add_obstacles_from_rects(self, rects: list, level_width: int, level_height: int) -> None:
        """Mark tiles occupied by the given rectangles as obstacles.

        Args:
            rects: List of pygame Rect objects.
            level_width: Level width in pixels.
            level_height: Level height in pixels.
        """
        self.width = level_width // TILE_SIZE
        self.height = level_height // TILE_SIZE
        for rect in rects:
            min_tx = max(0, rect.left // TILE_SIZE)
            min_ty = max(0, rect.top // TILE_SIZE)
            max_tx = min(self.width - 1, rect.right // TILE_SIZE)
            max_ty = min(self.height - 1, rect.bottom // TILE_SIZE)
            for tx in range(min_tx, max_tx + 1):
                for ty in range(min_ty, max_ty + 1):
                    self.obstacles.add((tx, ty))

    def clear_obstacles(self) -> None:
        """Remove all obstacle markings."""
        self.obstacles.clear()
