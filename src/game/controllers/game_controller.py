from pathlib import Path

import pygame

from game.models.enemy import Enemy
from game.models.flare import Flare
from game.models.player import Player
from game.rendering.renderer import Renderer
from game.systems.level import Level
from game.systems.map_loader import load_map
from game.systems.object_pool import ObjectPool

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
FIXED_DT = 1.0 / TARGET_FPS
FLOOR_Y = SCREEN_HEIGHT - 32


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
        self.flare_pool: ObjectPool[Flare] = ObjectPool(
            factory=Flare,
            reset=lambda f: f.reset(),
            size=20,
        )
        self._throw_cooldown = 0.0
        self.enemies: list[Enemy] = []
        self.current_floor = 1
        self._floor_cooldown = 0.0
        self._setup_test_walls()
        self._setup_test_enemies()

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
        self.player.update(dt, keys, self.level)

        rotation_speed = 180.0
        if keys[pygame.K_q]:
            self.player.flashlight.rotate(-rotation_speed * dt)
        if keys[pygame.K_e]:
            self.player.flashlight.rotate(rotation_speed * dt)

        self._throw_cooldown = max(0.0, self._throw_cooldown - dt)
        if keys[pygame.K_f] and self._throw_cooldown <= 0:
            self._throw_flare()
            self._throw_cooldown = 1.0

        for flare in self.flare_pool.active:
            flare.update(dt, FLOOR_Y)

        wall_rects = [w.rect for w in self.level.walls]
        grid = self.level.pathfinding_grid
        for enemy in self.enemies:
            has_los = enemy.can_see_optimized(self.player.x, self.player.y, self.level)
            enemy.update_suspicion(detected=has_los, dt=dt)
            enemy.tick_behavior_tree(self.player, self.player.rect, wall_rects, grid, dt)

        if self.player.health.is_dead:
            self.running = False

        self._floor_cooldown = max(0.0, self._floor_cooldown - dt)
        if keys[pygame.K_RETURN] and self._floor_cooldown <= 0:
            self._advance_floor()
            self._floor_cooldown = 2.0

    def _render(self) -> None:
        """Draw the current frame to the screen with multiply blending."""
        self.renderer.render(self.player, self.level, self.flare_pool.active, self.enemies)
        self.renderer.draw_hud(self.current_floor, self.player.health.ratio)

    def _setup_test_walls(self) -> None:
        """Load walls from the test map file."""
        map_path = Path(__file__).parent.parent / "game" / "maps" / "test_level.txt"
        load_map(str(map_path), self.level)

    def _setup_test_enemies(self) -> None:
        """Spawn placeholder enemies for development."""
        spawn_points = [(200, 200), (600, 300), (900, 150)]
        for x, y in spawn_points:
            self.enemies.append(Enemy(x, y))

    def _throw_flare(self) -> None:
        """Launch a flare from the player position in the facing direction."""
        import math

        flare = self.flare_pool.acquire()
        if flare is None:
            return

        angle = math.radians(self.player.flashlight.angle)
        flare.launch(
            x=self.player.x,
            y=self.player.y,
            angle=angle,
            speed=300.0,
        )

    def _advance_floor(self) -> None:
        """Progress to the next floor and reset the level."""
        self.current_floor += 1
        self.player.x = SCREEN_WIDTH / 2
        self.player.y = SCREEN_HEIGHT / 2
        self.player.rect.center = (int(self.player.x), int(self.player.y))
        self.enemies.clear()
        self._setup_test_walls()
        self._setup_test_enemies()
        self.flare_pool.release_all()
