import math
from typing import TYPE_CHECKING, Literal

import pygame

if TYPE_CHECKING:
    from models.wall import Wall
    from systems.level import Level


class Flare:
    """Throwable chemical flare that emits light and burns out over time."""

    GRAVITY = 0.0
    LIFETIME = 15.0
    BOUNCE_DAMPING = 0.4
    FRICTION_DAMPING = 0.995
    SKIN = 0

    def __init__(self) -> None:
        """Initialize an inactive flare."""
        self.reset()

    def reset(self) -> None:
        """Reset flare to inactive state."""
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.active = False
        self.elapsed = 0.0
        self.rect = pygame.Rect(0, 0, 8, 8)
        self.collision_rect = pygame.Rect(0, 0, 8, 8)

    def launch(self, x: float, y: float, angle: float, speed: float) -> None:
        """Launch the flare from a position at a given angle and speed.

        Args:
            x: Launch x coordinate.
            y: Launch y coordinate.
            angle: Launch angle in radians.
            speed: Initial velocity magnitude.
        """
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x - 4, y - 4, 8, 8)
        self.collision_rect = self.rect.inflate(-self.SKIN * 2, -self.SKIN * 2)
        self.angle = angle
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.active = True
        self.elapsed = 0.0

    def update(self, dt: float, level: Level) -> None:
        """Update flare physics for one frame.

        Args:
            dt: Delta time in seconds.
            level: Level containing walls for collision checks.
        """
        if not self.active:
            return

        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.active = False
            return

        self.vy += self.GRAVITY * dt

        for axis in ("x", "y"):
            setattr(self, "v" + axis, getattr(self, "v" + axis) * self.FRICTION_DAMPING)
            displacement = getattr(self, "v" + axis) * dt
            setattr(self, axis, getattr(self, axis) + displacement)
            setattr(self.collision_rect, "center" + axis, int(getattr(self, axis)))
            for wall in level.get_nearby_walls(self.collision_rect):
                self._resolve_collision(wall, displacement, axis)

        self.rect.center = (int(self.x), int(self.y))

    def _resolve_collision(self, wall: Wall, displacement: float, axis: Literal["x", "y"]) -> None:
        """Resolve overlap with a single wall along the given axis.

        Args:
            wall: Wall to check against.
            displacement: Signed movement amount this frame.
            axis: Either "x" or "y".
        """
        if not self.collision_rect.colliderect(wall.rect):
            return

        if axis == "x":
            if displacement > 0 and self.collision_rect.right > wall.rect.left:
                self.collision_rect.right = wall.rect.left
                self.x = self.collision_rect.centerx
            elif displacement < 0 and self.collision_rect.left < wall.rect.right:
                self.collision_rect.left = wall.rect.right
                self.x = self.collision_rect.centerx
            self.vx = -self.vx * self.BOUNCE_DAMPING
        else:
            if displacement > 0 and self.collision_rect.bottom > wall.rect.top:
                self.collision_rect.bottom = wall.rect.top
                self.y = self.collision_rect.centery
            elif displacement < 0 and self.collision_rect.top < wall.rect.bottom:
                self.collision_rect.top = wall.rect.bottom
                self.y = self.collision_rect.centery
            self.vy = -self.vy * self.BOUNCE_DAMPING

    @property
    def intensity(self) -> float:
        """Current brightness based on remaining lifetime."""
        remaining = max(0.0, self.LIFETIME - self.elapsed)
        t = remaining / self.LIFETIME
        return math.log(1 + 99 * t, 100)
