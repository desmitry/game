from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from rendering.lightmap import Lightmap


class Flashlight:
    """Directional flashlight that projects a cone of light."""

    def __init__(
        self,
        angle: float = 0.0,
        fov: float = 45.0,
        range_: float = 250.0,
        intensity: float = 0.95,
    ) -> None:
        """Initialize flashlight with direction and cone properties.

        Args:
            angle: Facing angle in degrees (0 = right, 90 = down).
            fov: Field of view cone width in degrees.
            range_: Maximum light reach in pixels.
            intensity: Brightness multiplier from 0.0 to 1.0.
        """
        self.angle = angle
        self.fov = fov
        self.range = range_
        self.intensity = intensity
        self.battery = 100.0
        self.max_battery = 100.0
        self.drain_rate = 2.0  # per second

    @property
    def battery_ratio(self) -> float:
        """Current battery as a fraction of maximum."""
        return self.battery / self.max_battery if self.max_battery > 0 else 0.0

    def draw(self, lightmap: Lightmap, x: float, y: float) -> None:
        """Draw the flashlight cone onto the given lightmap.

        Args:
            lightmap: Lightmap instance to draw onto.
            x: Origin x coordinate.
            y: Origin y coordinate.
        """
        half_fov = self.fov / 2
        steps = 32
        start_angle = self.angle - half_fov
        step_size = self.fov / steps

        for i in range(steps):
            ray_angle = start_angle + step_size * i
            ray_angle_rad = math.radians(ray_angle)
            ray_angle_next = math.radians(ray_angle + step_size)

            end_x = x + math.cos(ray_angle_rad) * self.range
            end_y = y + math.sin(ray_angle_rad) * self.range
            end_x_next = x + math.cos(ray_angle_next) * self.range
            end_y_next = y + math.sin(ray_angle_next) * self.range

            # Fade intensity toward edges of cone and distance
            edge_factor = 1.0 - abs((i - steps / 2) / (steps / 2)) ** 2
            dist_factor = 0.7
            alpha = int(self.intensity * 255 * edge_factor * dist_factor)

            points = [
                (x, y),
                (end_x, end_y),
                (end_x_next, end_y_next),
            ]
            pygame.draw.polygon(
                lightmap.surface,
                (255, 255, 255, alpha),
                points,
            )

    def rotate(self, delta: float) -> None:
        """Rotate the flashlight by the given delta angle.

        Args:
            delta: Angle change in degrees.
        """
        self.angle = (self.angle + delta) % 360

    def update(self, dt: float) -> None:
        """Drain battery over time.

        Args:
            dt: Delta time in seconds.
        """
        self.battery = max(0.0, self.battery - self.drain_rate * dt)
        if self.battery <= 0.0:
            self.intensity = 0.0

    def recharge(self, amount: float) -> None:
        """Add battery charge.

        Args:
            amount: Battery amount to add.
        """
        self.battery = min(self.max_battery, self.battery + amount)
        if self.battery > 0.0 and self.intensity == 0.0:
            self.intensity = 0.95
