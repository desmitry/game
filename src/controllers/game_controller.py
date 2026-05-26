import math
import random
from pathlib import Path

import pygame

from audio.sound_manager import SoundManager
from config import BEST_SCORE_PATH, SAVE_PATH, SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_FPS
from models.enemy import Enemy
from models.flare import Flare
from models.pickup import Pickup
from models.player import Player
from models.trapdoor import Trapdoor
from rendering.renderer import Renderer
from systems.genetic_algorithm import GeneticAlgorithm
from systems.level import Level
from systems.map_loader import load_map
from systems.object_pool import ObjectPool

FIXED_DT = 1.0 / TARGET_FPS
FLOOR_Y = SCREEN_HEIGHT - 32


class GameController:
    """Controls game logic, updates, and rendering for the playing state."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Inititialize game state, player, level, renderer, pools, and GA.

        Args:
            screen: Surface to render the game onto.
        """
        self.screen = screen
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_scale = 1.0
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
        self.trapdoor: Trapdoor | None = None
        self.genetic_algorithm = GeneticAlgorithm()
        self.current_floor = 1
        self._accumulator = 0.0
        self._pause_just_pressed = False
        self._died = False
        self._death_timer = 0.0
        self._new_record = False
        self._load_save()
        self.sound_manager = SoundManager()
        self._setup_audio()
        self._setup_test_walls()
        self._setup_test_enemies()
        self._setup_pickups()
        self._setup_trapdoor()

    def _load_save(self) -> None:
        """Restore GA and floor progress from a save file if available."""
        if self.genetic_algorithm.load(str(SAVE_PATH)):
            self.current_floor = max(1, self.genetic_algorithm.generation + 1)

    def _save_best_score(self) -> None:
        """Persist the deepest floor reached to a permanent file."""
        import json

        data = {"best_floor": self.genetic_algorithm.best_floor}
        with BEST_SCORE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event (for pause toggling and quit).

        Args:
            event: Pygame event to process.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = not self.paused
        elif event.type == pygame.QUIT:
            self.running = False
        elif (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._throw_cooldown <= 0
        ):
            self._throw_flare()
            self._throw_cooldown = 1.0

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
        if self._died:
            self._draw_death_overlay(screen)

    def _update(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        """Process game logic for a single fixed timestep.

        Args:
            dt: Delta time in seconds.
            keys: Current keyboard state.
        """
        if self._died:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self.genetic_algorithm.reset_population()
                self.genetic_algorithm.save(str(SAVE_PATH))
                SAVE_PATH.unlink(missing_ok=True)
                self.running = False
            return

        self.player.update(dt, keys, self.level)
        self.player.flashlight.update(dt)

        if self.player.health.is_dead:
            self._died = True
            self._death_timer = 2.0
            self.sound_manager.play_sfx("death")
            self._new_record = self.genetic_algorithm.update_best_floor(self.current_floor)
            self._save_best_score()
            self.genetic_algorithm.save(str(SAVE_PATH))
            return

        sx, sy = pygame.mouse.get_pos()
        mx = (sx - self.viewport_x) / self.viewport_scale
        my = (sy - self.viewport_y) / self.viewport_scale
        dx = mx - self.player.x
        dy = my - self.player.y
        self.player.flashlight.angle = math.degrees(math.atan2(dy, dx)) % 360

        self._throw_cooldown = max(0.0, self._throw_cooldown - dt)

        for flare in self.flare_pool.active:
            flare.update(dt, self.level)

        self._update_pickups(dt)
        self._update_enemies(dt)

        if self.trapdoor and self.player.rect.colliderect(self.trapdoor.rect):
            self._advance_floor()

        if keys[pygame.K_MINUS]:
            self.sound_manager.set_music_volume(self.sound_manager.music_volume - 0.1 * dt)
        if keys[pygame.K_EQUALS]:
            self.sound_manager.set_music_volume(self.sound_manager.music_volume + 0.1 * dt)

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
            enemy.update_suspicion(
                detected=has_los,
                player_x=self.player.x,
                player_y=self.player.y,
                dt=dt,
            )
            enemy.tick_behavior_tree(
                self.player, self.player.rect, wall_rects, grid, dt, has_los=has_los
            )
            if enemy.is_alerted:
                self.genetic_algorithm.record_tracking_time(enemy.enemy_id, dt)

        self._resolve_enemy_collisions()

        damage_taken = previous_hp - self.player.health.current_hp
        if damage_taken > 0:
            for enemy in self.enemies:
                if enemy.is_alerted:
                    self.genetic_algorithm.record_damage(enemy.enemy_id, damage_taken)

    def _resolve_enemy_collisions(self) -> None:
        """Push overlapping enemies apart to prevent stacking."""
        for i in range(len(self.enemies)):
            for j in range(i + 1, len(self.enemies)):
                a = self.enemies[i]
                b = self.enemies[j]
                if not a.rect.colliderect(b.rect):
                    continue
                dx = a.x - b.x
                dy = a.y - b.y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < 1.0:
                    dx, dy = 1.0, 0.0
                    dist = 1.0
                overlap = 28 - dist
                push_x = (dx / dist) * overlap * 0.5
                push_y = (dy / dist) * overlap * 0.5
                a.x += push_x
                a.y += push_y
                b.x -= push_x
                b.y -= push_y
                a.rect.center = (int(a.x), int(a.y))
                b.rect.center = (int(b.x), int(b.y))

    def _render(self) -> None:
        """Draw the current frame to the screen with multiply blending."""
        self.renderer.render(
            self.player,
            self.level,
            self.flare_pool.active,
            self.enemies,
            self.trapdoor,
            self.pickups,
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

        from systems.text_renderer import TextRenderer

        text = TextRenderer()
        pause_surf = text.render("PAUSED", 36, (200, 200, 200))
        pause_rect = pause_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(pause_surf, pause_rect)

        hint_surf = text.render("Press ESC to resume", 36, (140, 140, 140))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(hint_surf, hint_rect)

    def _draw_death_overlay(self, screen: pygame.Surface) -> None:
        """Draw game-over overlay when the player dies.

        Args:
            screen: Pygame display surface.
        """
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        from systems.text_renderer import TextRenderer

        text = TextRenderer()
        game_over = text.render("GAME OVER", 48, (200, 40, 40))
        go_rect = game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(game_over, go_rect)

        hint = text.render("Returning to menu...", 28, (140, 140, 140))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(hint, hint_rect)

        depth = self.current_floor - 1
        floor_text = text.render(f"Depth reached: {depth}", 28, (140, 140, 140))
        ft_rect = floor_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(floor_text, ft_rect)

        if self._new_record:
            record = text.render("NEW RECORD!", 28, (60, 200, 60))
            rec_rect = record.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            screen.blit(record, rec_rect)

    def _setup_test_walls(self) -> None:
        """Load walls from the test map file."""
        map_path = Path(__file__).parent.parent / "maps" / "test_level.txt"
        load_map(str(map_path), self.level)

    def _setup_test_enemies(self) -> None:
        """Spawn enemies using GA population genomes, avoiding walls and player."""
        candidate_spawns = [
            (200, 200),
            (400, 150),
            (700, 200),
            (1000, 150),
            (300, 450),
            (500, 550),
            (800, 500),
            (1050, 450),
            (250, 300),
            (900, 300),
            (600, 600),
            (1100, 350),
        ]
        valid_spawns: list[tuple[float, float]] = []
        for x, y in candidate_spawns:
            test_rect = pygame.Rect(x - 14, y - 14, 28, 28)
            blocked_by_wall = any(test_rect.colliderect(w.rect) for w in self.level.walls)
            too_close_to_player = ((x - self.player.x) ** 2 + (y - self.player.y) ** 2) ** 0.5 < 200  # noqa: PLR2004
            if not blocked_by_wall and not too_close_to_player:
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
        self.player.health.heal(9999)
        self.enemies.clear()
        self._setup_test_walls()
        self._setup_test_enemies()
        self._setup_pickups()
        self._setup_trapdoor()
        self.flare_pool.release_all()

    def _setup_pickups(self) -> None:
        """Place battery pickups in the level."""
        positions = [(450, 300), (600, 500), (400, 550)]
        self.pickups = [Pickup(x, y) for x, y in positions]

    def _setup_trapdoor(self) -> None:
        """Place the floor exit hatch on a random valid tile."""
        candidates = []
        for tx in range(40):
            for ty in range(21):
                wx = tx * 32 + 16
                wy = ty * 32 + 16
                tr = pygame.Rect(wx - 16, wy - 16, 32, 32)
                blocked = any(tr.colliderect(w.rect) for w in self.level.walls)
                if blocked:
                    continue
                dist_to_player = ((wx - self.player.x) ** 2 + (wy - self.player.y) ** 2) ** 0.5
                if dist_to_player > 300:  # noqa: PLR2004
                    candidates.append((wx, wy))
        if candidates:
            x, y = random.choice(candidates)  # noqa: S311
            self.trapdoor = Trapdoor(x, y)
        else:
            self.trapdoor = Trapdoor(SCREEN_WIDTH / 2, 100)

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
