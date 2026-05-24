from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.rendering.lightmap import Lightmap
from game.systems.text_renderer import TextRenderer

if TYPE_CHECKING:
    from game.models.enemy import Enemy
    from game.models.flare import Flare
    from game.models.pickup import Pickup
    from game.models.player import Player
    from game.systems.level import Level

LOW_BAT_THRESHOLD = 0.2


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
        self._text = TextRenderer()

    def render(
        self,
        player: Player,
        level: Level,
        flares: list[Flare],
        enemies: list[Enemy],
        pickups: list[Pickup] | None = None,
    ) -> None:
        """Draw the complete scene including lighting and walls.

        Args:
            player: Player model to render.
            level: Level containing walls and spatial grid.
            flares: Active flare list for light and rendering.
            enemies: Enemy list for rendering.
            pickups: Pickup items to render.
        """
        self.screen.fill((0, 0, 0))

        self._draw_walls(level)
        self._draw_pickups(pickups)
        pygame.draw.rect(self.screen, (128, 128, 128), player.rect)
        self._draw_flares(flares)

        for enemy in enemies:
            pygame.draw.rect(self.screen, enemy.color, enemy.rect)

        self._build_lightmap(player, flares)
        self.lightmap.apply_gamma()
        self._apply_multiply()

        pygame.display.flip()

    def _draw_walls(self, level: Level) -> None:
        """Draw wall rectangles.

        Args:
            level: Level with walls.
        """
        for wall in level.walls:
            pygame.draw.rect(self.screen, (80, 80, 80), wall.rect)

    def _draw_pickups(self, pickups: list[Pickup] | None) -> None:
        """Draw visible pickup items.

        Args:
            pickups: Pickup list or None.
        """
        if not pickups:
            return
        for pickup in pickups:
            if not pickup.collected:
                pygame.draw.rect(self.screen, (50, 200, 50), pickup.rect)

    def _draw_flares(self, flares: list[Flare]) -> None:
        """Draw active flare markers.

        Args:
            flares: Active flares list.
        """
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

    def _build_lightmap(self, player: Player, flares: list[Flare]) -> None:
        """Clear and populate the lightmap with flashlight and flare light.

        Args:
            player: Player with flashlight.
            flares: Active flares.
        """
        self.lightmap.clear()
        player.flashlight.draw(self.lightmap, player.x, player.y)

        for flare in flares:
            if flare.active:
                self.lightmap.draw_light(
                    flare.x,
                    flare.y,
                    radius=150.0 * flare.intensity,
                    color=(255, 140, 50),
                    intensity=flare.intensity * 0.9,
                )

    def _apply_multiply(self) -> None:
        """Blend lightmap over the scene using multiply."""
        darkened = self.screen.copy()
        darkened.blit(self.lightmap.surface, (0, 0), special_flags=pygame.BLEND_MULT)
        self.screen.blit(darkened, (0, 0))

    def draw_hud(
        self, floor: int, health_ratio: float, battery_ratio: float, flare_count: int
    ) -> None:
        """Render heads-up display overlay.

        Args:
            floor: Current floor number.
            health_ratio: Player health as a fraction from 0.0 to 1.0.
            battery_ratio: Flashlight battery as a fraction.
            flare_count: Number of flares available.
        """
        floor_surf = self._text.render(f"Floor {floor}", 24, (200, 200, 200))
        self.screen.blit(floor_surf, (10, 10))

        hp_bar_width = 150
        hp_bar_height = 12
        hp_x = self.screen.get_width() - hp_bar_width - 10
        hp_y = 10
        pygame.draw.rect(self.screen, (60, 60, 60), (hp_x, hp_y, hp_bar_width, hp_bar_height))
        fill_width = int(hp_bar_width * health_ratio)
        low_hp_threshold = 0.3
        color = (200, 50, 50) if health_ratio < low_hp_threshold else (50, 200, 50)
        pygame.draw.rect(self.screen, color, (hp_x, hp_y, fill_width, hp_bar_height))

        # Battery bar below HP
        bat_y = hp_y + hp_bar_height + 6
        pygame.draw.rect(self.screen, (60, 60, 60), (hp_x, bat_y, hp_bar_width, hp_bar_height))
        bat_fill = int(hp_bar_width * battery_ratio)
        bat_color = (50, 100, 200) if battery_ratio > LOW_BAT_THRESHOLD else (200, 50, 50)
        pygame.draw.rect(self.screen, bat_color, (hp_x, bat_y, bat_fill, hp_bar_height))

        # Flare count text
        flare_surf = self._text.render(f"Flares: {flare_count}/20", 24, (200, 200, 200))
        self.screen.blit(flare_surf, (10, 30))
