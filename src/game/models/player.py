import pygame


class Player:
    """Represents the player character with position and movement state."""

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

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        """Update player position based on pressed keys.

        Args:
            dt: Delta time in seconds.
            keys: Current keyboard state from pygame.key.get_pressed().
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

        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))
