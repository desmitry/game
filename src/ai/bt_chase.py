from __future__ import annotations

from typing import TYPE_CHECKING

from ai.astar import astar
from ai.bt_actions import move_with_collision
from ai.bt_node import BTNode, NodeState
from ai.pathfinding_grid import TILE_SIZE, PathfindingGrid

if TYPE_CHECKING:
    import pygame

    from models.enemy import Enemy

DIRECT_CHASE_DIST = TILE_SIZE * 3


class ChaseAction(BTNode):
    """Action node that uses A* to pathfind toward the player."""

    PATH_RECALC_INTERVAL = 0.5
    ATTACK_RANGE = 30.0
    ATTACK_DAMAGE = 15.0
    ATTACK_COOLDOWN = 1.5

    def __init__(self) -> None:
        """Initialize chase action with recalculation timer."""
        self._path: list[tuple[int, int]] = []
        self._path_index = 0
        self._recalc_timer = 0.0
        self._attack_timer = 0.0

    def _tick(self, context: dict) -> NodeState:
        """Navigate toward the player using A* pathfinding.

        Args:
            context: Behavior tree context with enemy, player, grid.

        Returns:
            RUNNING always so the action continues chasing each frame.
        """
        enemy = context["enemy"]
        player_rect = context["player_rect"]
        grid = context["grid"]
        dt = context.get("dt", 0.016)

        player_dist = (
            (enemy.x - player_rect.centerx) ** 2 + (enemy.y - player_rect.centery) ** 2
        ) ** 0.5

        self._recalc_timer -= dt
        if self._recalc_timer <= 0 and player_dist >= DIRECT_CHASE_DIST:
            self._recalc_timer = self.PATH_RECALC_INTERVAL
            self._path = self._compute_path(enemy, player_rect, grid)
            self._path_index = 0

        moved = False
        if self._path and self._path_index < len(self._path):
            target_tx, target_ty = self._path[self._path_index]
            target_x = target_tx * TILE_SIZE + TILE_SIZE / 2
            target_y = target_ty * TILE_SIZE + TILE_SIZE / 2

            dx = target_x - enemy.x
            dy = target_y - enemy.y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < enemy.ARRIVAL_THRESHOLD:
                self._path_index += 1
            else:
                move_x = (dx / dist) * enemy.speed * 1.5 * dt
                move_y = (dy / dist) * enemy.speed * 1.5 * dt
                move_with_collision(enemy, move_x, move_y, context["level"])
                moved = True

        if not moved:
            dx = player_rect.centerx - enemy.x
            dy = player_rect.centery - enemy.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > enemy.ARRIVAL_THRESHOLD:
                move_x = (dx / dist) * enemy.speed * 1.5 * dt
                move_y = (dy / dist) * enemy.speed * 1.5 * dt
                move_with_collision(enemy, move_x, move_y, context["level"])

        self._attack_timer -= dt
        if player_dist < self.ATTACK_RANGE and self._attack_timer <= 0:
            player = context.get("player")
            if player and player.health:
                player.health.take_damage(self.ATTACK_DAMAGE)
                self._attack_timer = self.ATTACK_COOLDOWN

        return NodeState.RUNNING

    def _compute_path(
        self, enemy: Enemy, player_rect: pygame.Rect, grid: PathfindingGrid
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
