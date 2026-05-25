from __future__ import annotations

import pygame

PICKUP_SIZE = 12


class Pickup:
    """A collectible item in the game world."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize pickup at the given position.

        Args:
            x: World x coordinate.
            y: World y coordinate.
        """
        self.x = x
        self.y = y
        half = PICKUP_SIZE // 2
        self.rect = pygame.Rect(x - half, y - half, PICKUP_SIZE, PICKUP_SIZE)
        self.collected = False
        self.respawn_timer = 0.0
        self.respawn_delay = 10.0

    def collect(self) -> None:
        """Mark as collected and start respawn timer."""
        self.collected = True
        self.respawn_timer = self.respawn_delay

    def update(self, dt: float) -> None:
        """Count down respawn timer if collected.

        Args:
            dt: Delta time in seconds.
        """
        if self.collected:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.collected = False
