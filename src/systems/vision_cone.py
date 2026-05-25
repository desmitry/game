import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class VisionCone:
    """Enemy vision cone that checks lightmap values for detection."""

    def __init__(self, angle: float = 0.0, fov: float = 60.0, range_: float = 200.0) -> None:
        """Initialize vision cone with direction and coverage.

        Args:
            angle: Facing angle in degrees.
            fov: Field of view width in degrees.
            range_: Maximum sight distance in pixels.
        """
        self.angle = angle
        self.fov = fov
        self.range = range_

    def is_in_cone(
        self,
        target_x: float,
        target_y: float,
        origin_x: float,
        origin_y: float,
    ) -> bool:
        """Check if a point falls within the vision cone.

        Args:
            target_x: Target x coordinate.
            target_y: Target y coordinate.
            origin_x: Cone origin x coordinate.
            origin_y: Cone origin y coordinate.

        Returns:
            True if the point is within cone angle and range.
        """
        dx = target_x - origin_x
        dy = target_y - origin_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > self.range or dist < 1.0:
            return False

        angle_to_target = math.degrees(math.atan2(dy, dx))
        angle_diff = abs((angle_to_target - self.angle + 180) % 360 - 180)

        return angle_diff <= self.fov / 2

    def check_brightness(
        self, lightmap_surface: pygame.Surface, origin_x: float, origin_y: float
    ) -> float:
        """Sample lightmap brightness at the cone center.

        Args:
            lightmap_surface: Lightmap surface to sample.
            origin_x: Cone origin x coordinate.
            origin_y: Cone origin y coordinate.

        Returns:
            Normalized brightness value from 0.0 to 1.0.
        """
        x = int(origin_x + math.cos(math.radians(self.angle)) * self.range * 0.5)
        y = int(origin_y + math.sin(math.radians(self.angle)) * self.range * 0.5)

        if not lightmap_surface.get_rect().collidepoint(x, y):
            return 0.0

        color = lightmap_surface.get_at((x, y))
        return sum(color[:3]) / (3 * 255)
