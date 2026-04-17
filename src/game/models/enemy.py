import pygame


class Enemy:
    """Base enemy entity with position and patrol state."""

    ARRIVAL_THRESHOLD = 4.0

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
