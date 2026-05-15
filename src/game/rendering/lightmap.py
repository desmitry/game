import pygame


class Lightmap:
    """RenderTarget surface for accumulating light sources before blending."""

    AMBIENT = (3, 3, 3)

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
        """Reset the lightmap to near-black (total darkness)."""
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

        gradient = pygame.Surface((diameter, diameter))
        gradient.fill(self.AMBIENT)
        center = int(radius)
        gamma = 1.6

        for r in range(center, 0, -1):
            t = r / center
            brightness = int((t**gamma) * 255 * intensity)
            c = (
                min(255, color[0] * brightness // 255),
                min(255, color[1] * brightness // 255),
                min(255, color[2] * brightness // 255),
            )
            pygame.draw.circle(gradient, c, (center, center), r)

        self.surface.blit(
            gradient,
            (x - radius, y - radius),
            special_flags=pygame.BLEND_RGB_ADD,
        )

    def apply_gamma(self) -> None:
        """Apply gamma correction for better dark visibility using a lookup surface."""
        width = 256
        lut = pygame.Surface((width, 1))
        for i in range(width):
            corrected = min(255, int(255.0 * ((i / 255.0) ** (1.0 / 1.6))))
            lut.set_at((i, 0), (corrected, corrected, corrected))

        scaled = pygame.transform.scale(self.surface, (width, 1))
        mapped = pygame.Surface((width, 1))
        for x in range(width):
            r, g, b, *_ = scaled.get_at((x, 0))
            avg = (r + g + b) // 3
            mapped.set_at((x, 0), lut.get_at((avg, 0)))

        scaled_mapped = pygame.transform.scale(mapped, (self.width, self.height))
        self.surface.blit(scaled_mapped, (0, 0), special_flags=pygame.BLEND_MULT)
