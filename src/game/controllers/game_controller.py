from pathlib import Path

import pygame

from game.audio.sound_manager import SoundManager
from game.models.enemy import Enemy
from game.models.flare import Flare
from game.models.pickup import Pickup
from game.models.player import Player
from game.rendering.renderer import Renderer
from game.systems.genetic_algorithm import GeneticAlgorithm
from game.systems.level import Level
from game.systems.map_loader import load_map
from game.systems.object_pool import ObjectPool

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
FIXED_DT = 1.0 / TARGET_FPS
FLOOR_Y = SCREEN_HEIGHT - 32
SAVE_PATH = Path.home() / ".eclipsed_evolution_save.json"


class GameController:
    """Controls game logic, updates, and rendering for the playing state."""

    def __init__(self) -> None:
        """Inititialize game state, player, level, renderer, pools, and GA."""
        self.screen = pygame.display.get_surface()
        self.running = True
        self.paused = False
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
        self.pickups: list[Pickup] = []
        self.genetic_algorithm = GeneticAlgorithm()
        self.current_floor = 1
        self._floor_cooldown = 0.0
        self._accumulator = 0.0
        self._pause_just_pressed = False
        self._load_save()
        self.sound_manager = SoundManager()
        self._setup_audio()
        self._setup_test_walls()
        self._setup_test_enemies()
        self._setup_pickups()

    def _load_save(self) -> None:
        """Restore GA and floor progress from a save file if available."""
        if self.genetic_algorithm.load(str(SAVE_PATH)):
            self.current_floor = max(1, self.genetic_algorithm.generation + 1)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event (for pause toggling and quit).

        Args:
            event: Pygame event to process.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = not self.paused
        elif event.type == pygame.QUIT:
            self.running = False

    def tick(self, dt: float) -> None:
        """Advance the simulation by dt seconds with a fixed timestep.

        Args:
            dt: Delta time in seconds from the real clock.
        """
        max_frame_time = 0.25
        dt = min(dt, max_frame_time)
        self._accumulator += dt

        keys = pygame.key.get_pressed()
        while self._accumulator >= FIXED_DT:
            if not self.paused:
                self._update(FIXED_DT, keys)
            self._accumulator -= FIXED_DT

    def draw(self, screen: pygame.Surface) -> None:
        """Render the current frame and optional pause overlay.

        Args:
            screen: Pygame display surface.
        """
        self._render()
        if self.paused:
            self._draw_pause_overlay(screen)
        pygame.display.flip()

    def _update(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        """Process game logic for a single fixed timestep.

        Args:
            dt: Delta time in seconds.
            keys: Current keyboard state.
        """
        self.player.update(dt, keys, self.level)
        self.player.flashlight.update(dt)

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

        self._update_pickups(dt)
        self._update_enemies(dt)

        if keys[pygame.K_MINUS]:
            self.sound_manager.set_music_volume(self.sound_manager.music_volume - 0.1 * dt)
        if keys[pygame.K_EQUALS]:
            self.sound_manager.set_music_volume(self.sound_manager.music_volume + 0.1 * dt)

        if self.player.health.is_dead:
            self.sound_manager.play_sfx("death")
            self.genetic_algorithm.save(str(SAVE_PATH))
            self.running = False

        self._floor_cooldown = max(0.0, self._floor_cooldown - dt)
        if keys[pygame.K_RETURN] and self._floor_cooldown <= 0:
            self._advance_floor()
            self._floor_cooldown = 2.0

    def _update_enemies(self, dt: float) -> None:
        """Update all enemies and track GA fitness.

        Args:
            dt: Delta time in seconds.
        """
        wall_rects = [w.rect for w in self.level.walls]
        grid = self.level.pathfinding_grid

        previous_hp = self.player.health.current_hp

        for enemy in self.enemies:
            has_los = enemy.can_see_optimized(self.player.x, self.player.y, self.level)
            enemy.update_suspicion(detected=has_los, dt=dt)
            enemy.tick_behavior_tree(self.player, self.player.rect, wall_rects, grid, dt)
            if enemy.is_alerted:
                self.genetic_algorithm.record_tracking_time(enemy.enemy_id, dt)

        damage_taken = previous_hp - self.player.health.current_hp
        if damage_taken > 0:
            for enemy in self.enemies:
                if enemy.is_alerted:
                    self.genetic_algorithm.record_damage(enemy.enemy_id, damage_taken)

    def _render(self) -> None:
        """Draw the current frame to the screen with multiply blending."""
        self.renderer.render(
            self.player, self.level, self.flare_pool.active, self.enemies, self.pickups
        )
        self.renderer.draw_hud(
            self.current_floor,
            self.player.health.ratio,
            self.player.flashlight.battery_ratio,
            self.flare_pool.size - len(self.flare_pool.active),
        )

    def _draw_pause_overlay(self, screen: pygame.Surface) -> None:
        """Draw a semi-transparent pause overlay.

        Args:
            screen: Pygame display surface.
        """
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        from game.systems.text_renderer import TextRenderer

        text = TextRenderer()
        pause_surf = text.render("PAUSED", 36, (200, 200, 200))
        pause_rect = pause_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(pause_surf, pause_rect)

        hint_surf = text.render("Press ESC to resume", 36, (140, 140, 140))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(hint_surf, hint_rect)

    def _setup_test_walls(self) -> None:
        """Load walls from the test map file."""
        map_path = Path(__file__).parent.parent / "game" / "maps" / "test_level.txt"
        load_map(str(map_path), self.level)

    def _setup_test_enemies(self) -> None:
        """Spawn enemies using GA population genomes, avoiding wall overlaps."""
        spawn_points = [(200, 200), (600, 300), (900, 150)]
        valid_spawns: list[tuple[float, float]] = []
        for x, y in spawn_points:
            test_rect = pygame.Rect(x - 14, y - 14, 28, 28)
            if not any(test_rect.colliderect(w.rect) for w in self.level.walls):
                valid_spawns.append((x, y))
        if not valid_spawns:
            valid_spawns = [(100, 100)]
        for i, (x, y) in enumerate(valid_spawns):
            genome = self.genetic_algorithm.population[i % len(self.genetic_algorithm.population)]
            self.enemies.append(Enemy(x, y, genome=genome))

    def _setup_audio(self) -> None:
        """Load sound effects and start ambient track."""
        self.sound_manager.load_sfx("flare", "flare.wav")
        self.sound_manager.load_sfx("hit", "hit.wav")
        self.sound_manager.load_sfx("death", "death.wav")
        self.sound_manager.load_sfx("floor", "floor.wav")
        self.sound_manager.play_ambient("ambient.ogg")

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
        self.sound_manager.play_sfx("flare")

    def _advance_floor(self) -> None:
        """Progress to the next floor, evolve enemies, and reset the level."""
        self.genetic_algorithm.evolve()
        self.genetic_algorithm.save(str(SAVE_PATH))
        self.sound_manager.play_sfx("floor")
        self.current_floor += 1
        self.player.x = SCREEN_WIDTH / 2
        self.player.y = SCREEN_HEIGHT / 2
        self.player.rect.center = (int(self.player.x), int(self.player.y))
        self.enemies.clear()
        self._setup_test_walls()
        self._setup_test_enemies()
        self._setup_pickups()
        self.flare_pool.release_all()

    def _setup_pickups(self) -> None:
        """Place battery pickups in the level."""
        positions = [(300, 400), (700, 500), (1000, 200)]
        self.pickups = [Pickup(x, y) for x, y in positions]

    def _update_pickups(self, dt: float) -> None:
        """Update pickup respawn timers and check collection.

        Args:
            dt: Delta time in seconds.
        """
        for pickup in self.pickups:
            pickup.update(dt)
            if not pickup.collected and pickup.rect.colliderect(self.player.rect):
                pickup.collect()
                self.player.flashlight.recharge(25.0)
