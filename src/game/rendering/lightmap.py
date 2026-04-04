import pygame


class Lightmap:
    """RenderTarget surface for accumulating light sources before blending."""

    def __init__(self, width: int, height: int) -> None:
        """Create a lightmap surface sized to the screen.

        Args:
            width: Width of the lightmap in pixels.
            height: Height of the lightmap in pixels.
        """
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)

    def clear(self) -> None:
        """Reset the lightmap to fully opaque white (full illumination)."""
        self.surface.fill((255, 255, 255, 255))

    def draw_light(
        self,
        x: float,
        y: float,
        radius: float,
        color: tuple[int, int, int],
        intensity: float = 1.0,
    ) -> None:
        """Draw a radial gradient light onto the lightmap.

        Args:
            x: Center x coordinate of the light.
            y: Center y coordinate of the light.
            radius: Maximum reach of the light in pixels.
            color: RGB color tuple for the light.
            intensity: Brightness multiplier from 0.0 to 1.0.
        """
        diameter = int(radius * 2)
        if diameter <= 0:
            return

        gradient = pygame.Surface((diameter, diameter), flags=pygame.SRCALPHA)
        center = int(radius)

        for r in range(center, 0, -1):
            alpha = int((r / center) * 255 * intensity)
            pygame.draw.circle(
                gradient,
                (*color, alpha),
                (center, center),
                r,
            )

        self.surface.blit(gradient, (x - radius, y - radius))
