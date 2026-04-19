from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.systems.raycast import raycast

if TYPE_CHECKING:
    from game.systems.level import Level


class Enemy:
    """Base enemy entity with position and patrol state."""

    ARRIVAL_THRESHOLD = 4.0
    VISION_RADIUS = 200.0

    def __init__(self, x: float, y: float) -> None:
        """Initialize enemy at the given position.

        Args:
            x: Initial x coordinate.
            y: Initial y coordinate.
        """
        self.x = x
        self.y = y
        self.speed = 100.0
        self.rect = pygame.Rect(x - 14, y - 14, 28, 28)
        self.patrol_target_x = x
        self.patrol_target_y = y
        self.is_patrolling = True

    def update(self, dt: float) -> None:
        """Move enemy toward its current patrol target.

        Args:
            dt: Delta time in seconds.
        """
        dx = self.patrol_target_x - self.x
        dy = self.patrol_target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < self.ARRIVAL_THRESHOLD:
            self.is_patrolling = False
            return

        move_x = (dx / dist) * self.speed * dt
        move_y = (dy / dist) * self.speed * dt

        self.x += move_x
        self.y += move_y
        self.rect.center = (int(self.x), int(self.y))

    def set_patrol_target(self, x: float, y: float) -> None:
        """Assign a new patrol destination.

        Args:
            x: Target x coordinate.
            y: Target y coordinate.
        """
        self.patrol_target_x = x
        self.patrol_target_y = y
        self.is_patrolling = True

    def can_see(self, target_x: float, target_y: float, walls: list[pygame.Rect]) -> bool:
        """Check line of sight to a target point.

        Args:
            target_x: Target x coordinate.
            target_y: Target y coordinate.
            walls: List of wall rectangles that block vision.

        Returns:
            True if the target is within vision range and not blocked.
        """
        dx = target_x - self.x
        dy = target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > self.VISION_RADIUS:
            return False

        return raycast((self.x, self.y), (target_x, target_y), walls)

    def can_see_optimized(self, target_x: float, target_y: float, level: Level) -> bool:
        """Check line of sight using spatial grid optimization.

        Args:
            target_x: Target x coordinate.
            target_y: Target y coordinate.
            level: Level with spatial grid for wall queries.

        Returns:
            True if the target is within vision range and not blocked.
        """
        dx = target_x - self.x
        dy = target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > self.VISION_RADIUS:
            return False

        query_rect = pygame.Rect(
            min(self.x, target_x) - 16,
            min(self.y, target_y) - 16,
            abs(dx) + 32,
            abs(dy) + 32,
        )
        nearby_walls = level.get_nearby_walls(query_rect)
        wall_rects = [w.rect for w in nearby_walls]

        return raycast((self.x, self.y), (target_x, target_y), wall_rects)
