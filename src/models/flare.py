import pygame


class Flare:
    """Throwable chemical flare that emits light and burns out over time."""

    GRAVITY = 400.0
    LIFETIME = 8.0
    BOUNCE_DAMPING = 0.4

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

    def launch(self, x: float, y: float, angle: float, speed: float) -> None:
        """Launch the flare from a position at a given angle and speed.

        Args:
            x: Launch x coordinate.
            y: Launch y coordinate.
            angle: Launch angle in radians.
            speed: Initial velocity magnitude.
        """
        import math

        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.active = True
        self.elapsed = 0.0

    def update(self, dt: float, floor_y: float) -> None:
        """Update flare physics for one frame.

        Args:
            dt: Delta time in seconds.
            floor_y: Y coordinate of the ground level.
        """
        if not self.active:
            return

        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.active = False
            return

        self.vy += self.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y >= floor_y:
            self.y = floor_y
            self.vy = -self.vy * self.BOUNCE_DAMPING
            self.vx *= 0.8

        self.rect.center = (int(self.x), int(self.y))

    @property
    def intensity(self) -> float:
        """Current brightness based on remaining lifetime."""
        remaining = max(0.0, self.LIFETIME - self.elapsed)
        return remaining / self.LIFETIME
