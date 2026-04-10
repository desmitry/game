import pygame

from game.models.player import Player
from game.models.wall import Wall
from game.rendering.renderer import Renderer
from game.systems.level import Level

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
        self.level = Level(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        self._setup_test_walls()

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
        self.renderer.render(self.player, self.level)

    def _setup_test_walls(self) -> None:
        """Place temporary test walls for development."""
        wall_positions = [
            (200, 150, 32, 200),
            (400, 300, 200, 32),
            (700, 100, 32, 300),
            (800, 450, 250, 32),
            (300, 500, 150, 32),
        ]
        for x, y, w, h in wall_positions:
            self.level.add_wall(Wall(x, y, w, h))
