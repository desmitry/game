import pygame


class Wall:
    """Static wall segment used for collision and LOS blocking."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        """Create a wall at the given position and size.

        Args:
            x: Top-left x coordinate.
            y: Top-left y coordinate.
            width: Width in pixels.
            height: Height in pixels.
        """
        self.rect = pygame.Rect(x, y, width, height)
