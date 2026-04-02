import pygame

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

            while accumulator >= FIXED_DT:
                self._update(FIXED_DT)
                accumulator -= FIXED_DT

            self._render()

        pygame.quit()

    def _update(self, dt: float) -> None:
        """Process game logic for a single fixed timestep."""

    def _render(self) -> None:
        """Draw the current frame to the screen."""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
