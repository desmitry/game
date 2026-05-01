from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.models.flashlight import Flashlight
from game.models.health import Health

if TYPE_CHECKING:
    from game.models.wall import Wall
    from game.systems.level import Level


class Player:
    """Represents the player character with position and movement state."""

    SKIN = 2  # Collision skin shrink in pixels to allow wall sliding.

    def __init__(self, x: float, y: float) -> None:
        """Initialize player at the given position.

        Args:
            x: Initial x coordinate.
            y: Initial y coordinate.
        """
        self.x = x
        self.y = y
        self.speed = 200.0
        self.rect = pygame.Rect(x - 16, y - 16, 32, 32)
        self.collision_rect = self.rect.inflate(-self.SKIN * 2, -self.SKIN * 2)
        self.flashlight = Flashlight()
        self.health = Health(max_hp=100)
        self._attack_cooldown = 0.0

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, level: Level) -> None:
        """Update player position based on pressed keys with collision resolution.

        Args:
            dt: Delta time in seconds.
            keys: Current keyboard state from pygame.key.get_pressed().
            level: Level containing walls for collision checks.
        """
        dx, dy = self._read_input(keys)
        move_x = dx * self.speed * dt
        move_y = dy * self.speed * dt

        self._move_axis(move_x, move_y, level, axis="x")
        self._move_axis(move_x, move_y, level, axis="y")

        self.collision_rect.center = self.rect.center

    def _read_input(self, keys: pygame.key.ScancodeWrapper) -> tuple[float, float]:
        """Convert keyboard state to a normalized direction vector.

        Args:
            keys: Current keyboard state.

        Returns:
            Tuple of (dx, dy) normalized direction components.
        """
        dx = 0.0
        dy = 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        if dx != 0.0 and dy != 0.0:
            length = (dx * dx + dy * dy) ** 0.5
            dx /= length
            dy /= length

        return dx, dy

    def _move_axis(self, move_x: float, move_y: float, level: Level, axis: str) -> None:
        """Move the player along one axis and resolve wall collisions.

        Args:
            move_x: Horizontal displacement.
            move_y: Vertical displacement.
            level: Level containing walls.
            axis: Either "x" or "y".
        """
        if axis == "x":
            self.x += move_x
            self.collision_rect.centerx = int(self.x)
            displacement = move_x
        else:
            self.y += move_y
            self.collision_rect.centery = int(self.y)
            displacement = move_y

        for wall in level.get_nearby_walls(self.collision_rect):
            self._resolve_collision(wall, displacement, axis)

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def _resolve_collision(self, wall: Wall, displacement: float, axis: str) -> None:
        """Resolve overlap with a single wall along the given axis.

        Args:
            wall: Wall to check against.
            displacement: Signed movement amount this frame.
            axis: Either "x" or "y".
        """
        if not self.collision_rect.colliderect(wall.rect):
            return

        if axis == "x":
            if displacement > 0:
                self.collision_rect.right = wall.rect.left
            elif displacement < 0:
                self.collision_rect.left = wall.rect.right
            self.x = self.collision_rect.centerx
        elif displacement > 0:
            self.collision_rect.bottom = wall.rect.top
        elif displacement < 0:
            self.collision_rect.top = wall.rect.bottom
            self.y = self.collision_rect.centery
