import math
from typing import TYPE_CHECKING

import pygame

from game.ai.bt_actions import (
    CheckLineOfSight,
    CheckSuspicion,
    InvestigateLocation,
    MoveToPatrol,
    WanderAction,
)
from game.ai.bt_chase import ChaseAction
from game.ai.bt_composites import Selector, Sequence
from game.systems.genome import Genome
from game.systems.raycast import raycast
from game.systems.vision_cone import VisionCone

if TYPE_CHECKING:
    from game.ai.bt_node import BTNode
    from game.ai.pathfinding_grid import PathfindingGrid
    from game.models.player import Player
    from game.systems.level import Level


class Enemy:
    """Base enemy entity with position and patrol state."""

    ARRIVAL_THRESHOLD = 4.0
    SUSPICION_THRESHOLD = 0.8
    SUSPICION_DECAY_RATE = 0.3
    SUSPICION_GAIN_RATE = 1.5
    ENEMY_ID_COUNTER = 0

    def __init__(self, x: float, y: float, genome: Genome | None = None) -> None:
        """Initialize enemy at the given position.

        Args:
            x: Initial x coordinate.
            y: Initial y coordinate.
            genome: Optional genome to derive traits from.
        """
        self.enemy_id = Enemy.ENEMY_ID_COUNTER
        Enemy.ENEMY_ID_COUNTER += 1

        self.genome = genome or Genome()
        self.x = x
        self.y = y
        self.speed = self.genome.speed
        self.rect = pygame.Rect(x - 14, y - 14, 28, 28)
        self.patrol_target_x = x
        self.patrol_target_y = y
        self.is_patrolling = True
        self.vision_cone = VisionCone(range_=self.genome.vision)
        self.suspicion = 0.0
        self.last_known_player_x = x
        self.last_known_player_y = y
        self.is_alerted = False
        self.bt = self._build_behavior_tree()
        self.bt_context: dict = {"enemy": self}
        self.color = self._derive_color()

    @staticmethod
    def _gene_to_color(value: float, low: float, high: float, channel: int) -> int:
        """Map a gene value to a color channel intensity.

        Args:
            value: Gene value.
            low: Minimum expected gene value.
            high: Maximum expected gene value.
            channel: 0=R, 1=G, 2=B.

        Returns:
            Color channel value 0-255.
        """
        ratio = (value - low) / (high - low) if high > low else 0.5
        ratio = max(0.0, min(1.0, ratio))
        base = [0, 60, 100]
        variation = int(ratio * 155)
        base[channel] += variation
        return min(255, base[channel])

    def _derive_color(self) -> pygame.Color:
        """Compute a display colour from the genome by mapping each gene to an RGB channel.

        Returns:
            Pygame Color for rendering.
        """
        r = self._gene_to_color(self.genome.speed, Genome.MIN_SPEED, Genome.MAX_SPEED, 0)
        g = self._gene_to_color(self.genome.vision, Genome.MIN_VISION, Genome.MAX_VISION, 1)
        b = self._gene_to_color(self.genome.hearing, Genome.MIN_HEARING, Genome.MAX_HEARING, 2)
        return pygame.Color(r, g, b)

    def update(self, dt: float) -> None:
        """Move enemy toward its current patrol target.

        Args:
            dt: Delta time in seconds.
        """
        dx = self.patrol_target_x - self.x
        dy = self.patrol_target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < self.ARRIVAL_THRESHOLD:
            self.is_patrolling = False
            return

        self.vision_cone.angle = math.degrees(math.atan2(dy, dx))

        move_x = (dx / dist) * self.speed * dt
        move_y = (dy / dist) * self.speed * dt

        self.x += move_x
        self.y += move_y
        self.rect.center = (int(self.x), int(self.y))

    def set_patrol_target(self, x: float, y: float) -> None:
        """Assign a new patrol destination.

        Args:
            x: Target x coordinate.
            y: Target y coordinate.
        """
        self.patrol_target_x = x
        self.patrol_target_y = y
        self.is_patrolling = True

    def can_see(self, target_x: float, target_y: float, walls: list[pygame.Rect]) -> bool:
        """Check line of sight to a target point.

        Args:
            target_x: Target x coordinate.
            target_y: Target y coordinate.
            walls: List of wall rectangles that block vision.

        Returns:
            True if the target is within vision range and not blocked.
        """
        dx = target_x - self.x
        dy = target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > self.genome.vision:
            return False

        return raycast((self.x, self.y), (target_x, target_y), walls)

    def can_see_optimized(self, target_x: float, target_y: float, level: Level) -> bool:
        """Check line of sight using spatial grid optimization.

        Args:
            target_x: Target x coordinate.
            target_y: Target y coordinate.
            level: Level with spatial grid for wall queries.

        Returns:
            True if the target is within vision range and not blocked.
        """
        dx = target_x - self.x
        dy = target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > self.genome.vision:
            return False

        query_rect = pygame.Rect(
            min(self.x, target_x) - 16,
            min(self.y, target_y) - 16,
            abs(dx) + 32,
            abs(dy) + 32,
        )
        nearby_walls = level.get_nearby_walls(query_rect)
        wall_rects = [w.rect for w in nearby_walls]

        return raycast((self.x, self.y), (target_x, target_y), wall_rects)

    def update_suspicion(self, *, detected: bool, dt: float) -> None:
        """Update suspicion meter with hysteresis behavior.

        Args:
            detected: Whether the player is currently detected.
            dt: Delta time in seconds.
        """
        if detected:
            self.suspicion = min(
                1.0,
                self.suspicion + self.SUSPICION_GAIN_RATE * dt,
            )
            self.last_known_player_x = self.vision_cone.angle
        else:
            self.suspicion = max(
                0.0,
                self.suspicion - self.SUSPICION_DECAY_RATE * dt,
            )

        if self.suspicion >= self.SUSPICION_THRESHOLD:
            self.is_alerted = True
        elif self.suspicion <= 0.0:
            self.is_alerted = False

    def _build_behavior_tree(self) -> BTNode:
        """Construct the enemy's behavior tree.

        Returns:
            Root BTNode with Chase, Investigate, Patrol, and Wander branches.
        """
        return Selector(
            children=[
                Sequence(
                    children=[
                        CheckLineOfSight(),
                        ChaseAction(),
                    ]
                ),
                Sequence(
                    children=[
                        CheckSuspicion(),
                        InvestigateLocation(),
                    ]
                ),
                MoveToPatrol(),
                WanderAction(),
            ]
        )

    def tick_behavior_tree(
        self,
        player: Player,
        player_rect: pygame.Rect,
        walls: list[pygame.Rect],
        grid: PathfindingGrid,
        dt: float,
    ) -> None:
        """Execute the behavior tree for this frame.

        Args:
            player: Player object for health and attack checks.
            player_rect: Player bounding rectangle.
            walls: List of wall rectangles for LOS checks.
            grid: Pathfinding grid for chase navigation.
            dt: Delta time in seconds.
        """
        self.bt_context["player"] = player
        self.bt_context["player_rect"] = player_rect
        self.bt_context["walls"] = walls
        self.bt_context["grid"] = grid
        self.bt_context["dt"] = dt
        self.bt.tick(self.bt_context)
