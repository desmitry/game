from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.rendering.lightmap import Lightmap

if TYPE_CHECKING:
    from game.models.flare import Flare
    from game.models.player import Player
    from game.systems.level import Level


class Renderer:
    """Handles all rendering operations for the game scene."""

    def __init__(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Initialize renderer with the target screen.

        Args:
            screen: Pygame surface to render onto.
            width: Screen width in pixels.
            height: Screen height in pixels.
        """
        self.screen = screen
        self.lightmap = Lightmap(width, height)

    def render(self, player: Player, level: Level, flares: list[Flare]) -> None:
        """Draw the complete scene including lighting and walls.

        Args:
            player: Player model to render.
            level: Level containing walls and spatial grid.
            flares: Active flare list for light and rendering.
        """
        self.screen.fill((0, 0, 0))

        # Draw walls
        for wall in level.walls:
            pygame.draw.rect(self.screen, (80, 80, 80), wall.rect)

        # Draw scene elements
        pygame.draw.rect(self.screen, (128, 128, 128), player.rect)

        # Draw flares
        for flare in flares:
            if flare.active:
                alpha = int(flare.intensity * 255)
                pygame.draw.circle(
                    self.screen,
                    (255, 100, 50),
                    flare.rect.center,
                    4,
                )
                if alpha > 0:
                    pygame.draw.circle(
                        self.screen,
                        (255, 100, 50, alpha),
                        flare.rect.center,
                        8,
                        width=1,
                    )

        # Build lightmap
        self.lightmap.clear()
        player.flashlight.draw(self.lightmap, player.x, player.y)

        for flare in flares:
            if flare.active:
                self.lightmap.draw_light(
                    flare.x,
                    flare.y,
                    radius=120.0 * flare.intensity,
                    color=(255, 140, 50),
                    intensity=flare.intensity * 0.8,
                )

        # Apply multiply blending
        darkened = self.screen.copy()
        darkened.fill((20, 20, 20))
        darkened.blit(self.lightmap.surface, (0, 0), special_flags=pygame.BLEND_MULT)
        self.screen.blit(darkened, (0, 0))

        pygame.display.flip()
