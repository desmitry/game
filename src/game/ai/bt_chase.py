from __future__ import annotations

from typing import TYPE_CHECKING

from game.ai.astar import astar
from game.ai.bt_node import BTNode, NodeState
from game.ai.pathfinding_grid import TILE_SIZE

if TYPE_CHECKING:
    import pygame

    from game.ai.pathfinding_grid import PathfindingGrid
    from game.models.enemy import Enemy


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
        self,
        enemy: Enemy,
        player_rect: pygame.Rect,
        grid: PathfindingGrid,
    ) -> list[tuple[int, int]]:
        """Calculate A* path from enemy to player.

        Args:
            enemy: The chasing enemy.
            player_rect: Player bounding rectangle.
            grid: Pathfinding grid with obstacle data.

        Returns:
            List of tile coordinates forming the path.
        """
        start = grid.world_to_tile(enemy.x, enemy.y)
        goal = grid.world_to_tile(player_rect.centerx, player_rect.centery)
        return astar(grid, start, goal)
