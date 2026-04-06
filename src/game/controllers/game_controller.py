import pygame

from game.models.player import Player
from game.rendering.lightmap import Lightmap

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
FIXED_DT = 1.0 / TARGET_FPS


class GameController:
    """Controls the main game loop and fixed timestep updates."""

    def __init__(self) -> None:
        """Initialize pygame, create the display window, and setup the clock."""
        pygame.init()
        pygame.display.set_caption("Eclipsed Evolution")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = False
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.lightmap = Lightmap(SCREEN_WIDTH, SCREEN_HEIGHT)

    def run(self) -> None:
        """Execute the main game loop with fixed timestep."""
        self.running = True
        accumulator = 0.0

        while self.running:
            max_frame_time = 0.25
            frame_time = self.clock.tick(TARGET_FPS) / 1000.0
            frame_time = min(frame_time, max_frame_time)
            accumulator += frame_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            keys = pygame.key.get_pressed()
            while accumulator >= FIXED_DT:
                self._update(FIXED_DT, keys)
                accumulator -= FIXED_DT

            self._render()

        pygame.quit()

    def _update(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        """Process game logic for a single fixed timestep.

        Args:
            dt: Delta time in seconds.
            keys: Current keyboard state.
        """
        self.player.update(dt, keys)

        rotation_speed = 180.0
        if keys[pygame.K_q]:
            self.player.flashlight.rotate(-rotation_speed * dt)
        if keys[pygame.K_e]:
            self.player.flashlight.rotate(rotation_speed * dt)

    def _render(self) -> None:
        """Draw the current frame to the screen with multiply blending."""
        self.screen.fill((0, 0, 0))

        # Draw scene elements
        pygame.draw.rect(self.screen, (128, 128, 128), self.player.rect)

        # Build lightmap
        self.lightmap.clear()
        self.player.flashlight.draw(self.lightmap, self.player.x, self.player.y)

        # Apply multiply blending
        darkened = self.screen.copy()
        darkened.fill((20, 20, 20))
        darkened.blit(self.lightmap.surface, (0, 0), special_flags=pygame.BLEND_MULT)
        self.screen.blit(darkened, (0, 0))

        pygame.display.flip()
