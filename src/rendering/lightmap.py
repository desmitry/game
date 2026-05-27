import numpy as np
import pygame


class Lightmap:
    """RenderTarget surface for accumulating light sources before blending."""

    AMBIENT = (0, 0, 0)

    def __init__(self, width: int, height: int) -> None:
        """Create a lightmap surface sized to the screen.

        Args:
            width: Width of the lightmap in pixels.
            height: Height of the lightmap in pixels.
        """
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))

    def clear(self) -> None:
        """Reset the lightmap to darkness."""
        self.surface.fill(self.AMBIENT)

    def draw_light(
        self,
        x: float,
        y: float,
        radius: float,
        color: tuple[int, int, int],
        intensity: float = 1.0,
    ) -> None:
        """Draw a radial gradient light onto the lightmap using additive blending.

        Uses isotropic (omnidirectional) inverse-square falloff with a
        smooth fade to zero at the edge of the render radius.

        Args:
            x: Center x coordinate of the light.
            y: Center y coordinate of the light.
            radius: Render radius in pixels (light fades smoothly to 0 at this edge).
            color: RGB color tuple for the light.
            intensity: Brightness multiplier from 0.0 to 1.0.
        """
        diameter = int(radius * 2)
        if diameter <= 0:
            return

        gradient = pygame.Surface((diameter, diameter))
        gradient.fill(self.AMBIENT)
        center = int(radius)

        coords = np.arange(diameter) - center
        xx, yy = np.meshgrid(coords, coords, indexing="ij")

        dist_sq = xx * xx + yy * yy
        radius_sq = radius * radius

        inv_sq = 1.0 / (1.0 + dist_sq / radius_sq)
        edge_fade = np.clip(1.0 - dist_sq / radius_sq, 0.0, 1.0)
        dist_factor = inv_sq * edge_fade
        brightness = np.clip(255 * intensity * dist_factor, 0, 255).astype(np.uint8)

        brightness_f = brightness.astype(np.float32)
        arr = pygame.surfarray.pixels3d(gradient)
        arr[:, :, 0] = (brightness_f * color[0] / 255.0).clip(0, 255).astype(np.uint8)
        arr[:, :, 1] = (brightness_f * color[1] / 255.0).clip(0, 255).astype(np.uint8)
        arr[:, :, 2] = (brightness_f * color[2] / 255.0).clip(0, 255).astype(np.uint8)
        del arr

        self.surface.blit(
            gradient,
            (int(x) - radius, int(y) - radius),
            special_flags=pygame.BLEND_RGB_ADD,
        )
