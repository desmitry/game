from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pygame

if TYPE_CHECKING:
    from rendering.lightmap import Lightmap


class Flashlight:
    """Directional flashlight that projects a cone of light."""

    def __init__(
        self,
        angle: float = 0.0,
        fov: float = 70.0,
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
        self.drain_rate = 2.0
        self._gradient: pygame.Surface | None = None

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
        sigma = self.fov / 4
        size = int(self.range * 2)
        center = int(self.range)

        if self._gradient is None or self._gradient.get_width() != size:
            self._gradient = pygame.Surface((size, size))

        self._gradient.fill(lightmap.AMBIENT)

        coords = np.arange(size) - center
        xx, yy = np.meshgrid(coords, coords, indexing="ij")

        dist_sq = xx * xx + yy * yy
        range_sq = self.range * self.range

        dist_factor = np.maximum(0.0, 1.0 - dist_sq / range_sq)

        pixel_angle = np.degrees(np.arctan2(yy, xx))
        angle_diff = (pixel_angle - self.angle + 180) % 360 - 180
        angle_factor = np.exp(-(angle_diff * angle_diff) / (2 * sigma * sigma))

        brightness = 255.0 * self.intensity * dist_factor * angle_factor
        brightness = np.clip(brightness, 0, 255).astype(np.uint8)

        arr = pygame.surfarray.pixels3d(self._gradient)
        arr[:] = np.stack([brightness, brightness, brightness], axis=-1)
        del arr

        lightmap.surface.blit(
            self._gradient,
            (int(x) - center, int(y) - center),
            special_flags=pygame.BLEND_RGB_ADD,
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
