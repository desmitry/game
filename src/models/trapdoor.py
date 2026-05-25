from __future__ import annotations

import pygame


class Trapdoor:
    """A floor hatch that advances to the next level when stepped on."""

    SIZE = 32

    def __init__(self, x: float, y: float) -> None:
        """Initialize trapdoor at the given position.

        Args:
            x: Centre x coordinate.
            y: Centre y coordinate.
        """
        self.x = x
        self.y = y
        self.rect = pygame.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = (int(x), int(y))
