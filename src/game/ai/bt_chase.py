from __future__ import annotations

from typing import TYPE_CHECKING

from game.ai.astar import astar
from game.ai.bt_node import BTNode, NodeState
from game.ai.pathfinding_grid import TILE_SIZE, PathfindingGrid

if TYPE_CHECKING:
    import pygame

    from game.models.enemy import Enemy

PathNode = tuple[int, int]


class ChaseAction(BTNode):
    """Action node that uses A* to pathfind toward the player."""

    PATH_RECALC_INTERVAL = 0.5

    def __init__(self) -> None:
        """Initialize chase action with recalculation timer."""
        self._path: list[tuple[int, int]] = []
        self._path_index = 0
        self._recalc_timer = 0.0

    def _tick(self, context: dict) -> NodeState:
        """Navigate toward the player using A* pathfinding.

        Args:
            context: Behavior tree context with enemy, player, grid.

        Returns:
            RUNNING while chasing, SUCCESS when pathfinding fails.
        """
        enemy = context["enemy"]
        player_rect = context["player_rect"]
        grid = context["grid"]
        dt = context.get("dt", 0.016)

        self._recalc_timer -= dt
        if self._recalc_timer <= 0 or self._path_index >= len(self._path):
            self._recalc_timer = self.PATH_RECALC_INTERVAL
            self._path = self._compute_path(enemy, player_rect, grid)
            self._path_index = 0

        if not self._path:
            return NodeState.FAILURE

        if self._path_index >= len(self._path):
            return NodeState.SUCCESS

        target_tx, target_ty = self._path[self._path_index]
        target_x = target_tx * TILE_SIZE + TILE_SIZE / 2
        target_y = target_ty * TILE_SIZE + TILE_SIZE / 2

        dx = target_x - enemy.x
        dy = target_y - enemy.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < enemy.ARRIVAL_THRESHOLD:
            self._path_index += 1
            if self._path_index >= len(self._path):
                return NodeState.SUCCESS

        move_x = (dx / dist) * enemy.speed * 1.5 * dt
        move_y = (dy / dist) * enemy.speed * 1.5 * dt
        enemy.x += move_x
        enemy.y += move_y
        enemy.rect.center = (int(enemy.x), int(enemy.y))

        return NodeState.RUNNING

    def _compute_path(
        self, enemy: Enemy, player_rect: pygame.Rect, grid: PathfindingGrid
    ) -> list[PathNode]:
        """Calculate A* path from enemy to player with corner smoothing.

        Args:
            enemy: The chasing enemy.
            player_rect: Player bounding rectangle.
            grid: Pathfinding grid with obstacle data.

        Returns:
            List of tile coordinates forming the path.
        """
        start = grid.world_to_tile(enemy.x, enemy.y)
        goal = grid.world_to_tile(player_rect.centerx, player_rect.centery)
        path = astar(grid, start, goal)
        return _smooth_path(grid, path)


def _smooth_path(grid: PathfindingGrid, path: list[PathNode]) -> list[PathNode]:
    """Simplify path by skipping waypoints with clear line of sight.

    Args:
        grid: Pathfinding grid for clearance checks.
        path: Raw A* path.

    Returns:
        Simplified path avoiding tight corner cuts.
    """
    min_path_len = 2
    if len(path) <= min_path_len:
        return path

    smoothed = [path[0]]
    i = 0

    while i < len(path) - 1:
        for j in range(len(path) - 1, i, -1):
            if _has_clearance(grid, path[i], path[j]):
                i = j
                smoothed.append(path[i])
                break
        else:
            i += 1
            smoothed.append(path[i])

    return smoothed


def _has_clearance(grid: PathfindingGrid, a: PathNode, b: PathNode) -> bool:
    """Check if a straight line between two tiles has corner clearance.

    Args:
        grid: Pathfinding grid.
        a: Start tile.
        b: End tile.

    Returns:
        True if all tiles along the line plus clearance are valid.
    """
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return True

    step_x = dx / steps
    step_y = dy / steps

    for s in range(1, steps):
        x = a[0] + step_x * s
        y = a[1] + step_y * s
        for ox in range(-1, 2):
            for oy in range(-1, 2):
                if not grid.is_valid(int(x) + ox, int(y) + oy):
                    return False

    return True
