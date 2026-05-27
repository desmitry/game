from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ai.bt_node import BTNode, NodeState

if TYPE_CHECKING:
    from models.enemy import Enemy
    from systems.level import Level


def move_with_collision(
    enemy: Enemy,
    move_x: float,
    move_y: float,
    level: Level,
) -> None:
    """Move an enemy per-axis with wall collision resolution.

    Args:
        enemy: Enemy instance to move.
        move_x: Displacement along the x-axis.
        move_y: Displacement along the y-axis.
        level: Level containing walls for collision queries.
    """
    enemy.x += move_x
    enemy.rect.centerx = int(enemy.x)
    for wall in level.get_nearby_walls(enemy.rect):
        if enemy.rect.colliderect(wall.rect):
            if move_x > 0:
                enemy.rect.right = wall.rect.left
            elif move_x < 0:
                enemy.rect.left = wall.rect.right
            enemy.x = float(enemy.rect.centerx)

    enemy.y += move_y
    enemy.rect.centery = int(enemy.y)
    for wall in level.get_nearby_walls(enemy.rect):
        if enemy.rect.colliderect(wall.rect):
            if move_y > 0:
                enemy.rect.bottom = wall.rect.top
            elif move_y < 0:
                enemy.rect.top = wall.rect.bottom
            enemy.y = float(enemy.rect.centery)

    enemy.rect.center = (int(enemy.x), int(enemy.y))


class WanderAction(BTNode):
    """Action node that picks a random nearby patrol target."""

    def __init__(self, wander_radius: float = 150.0) -> None:
        """Initialize wander action with a radius.

        Args:
            wander_radius: Maximum distance for random patrol targets.
        """
        self.wander_radius = wander_radius

    def _tick(self, context: dict) -> NodeState:
        """Set a random patrol target for the enemy.

        Args:
            context: Behavior tree context containing 'enemy'.

        Returns:
            SUCCESS after setting a new patrol target.
        """
        enemy = context["enemy"]
        offset_x = random.uniform(-self.wander_radius, self.wander_radius)  # noqa: S311
        offset_y = random.uniform(-self.wander_radius, self.wander_radius)  # noqa: S311
        enemy.set_patrol_target(
            enemy.x + offset_x,
            enemy.y + offset_y,
        )
        return NodeState.SUCCESS


class MoveToPatrol(BTNode):
    """Action node that moves the enemy toward its patrol target."""

    def _tick(self, context: dict) -> NodeState:
        """Continue moving toward patrol target.

        Args:
            context: Behavior tree context containing 'enemy'.

        Returns:
            RUNNING while moving, SUCCESS when target is reached,
            FAILURE when no patrol target is set.
        """
        enemy = context["enemy"]
        dt = context.get("dt", 0.016)
        if not enemy.is_patrolling:
            return NodeState.FAILURE

        dx = enemy.patrol_target_x - enemy.x
        dy = enemy.patrol_target_y - enemy.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < enemy.ARRIVAL_THRESHOLD:
            enemy.is_patrolling = False
            return NodeState.SUCCESS

        move_x = (dx / dist) * enemy.speed * dt
        move_y = (dy / dist) * enemy.speed * dt
        move_with_collision(enemy, move_x, move_y, context["level"])
        return NodeState.RUNNING


class CheckSuspicion(BTNode):
    """Condition node that checks if suspicion exceeds the alert threshold."""

    def _tick(self, context: dict) -> NodeState:
        """Evaluate suspicion level.

        Args:
            context: Behavior tree context containing 'enemy'.

        Returns:
            SUCCESS if the enemy is alerted, FAILURE otherwise.
        """
        enemy = context["enemy"]
        if enemy.is_alerted:
            return NodeState.SUCCESS
        return NodeState.FAILURE


class CheckLineOfSight(BTNode):
    """Condition node that checks if the enemy can see the player."""

    def _tick(self, context: dict) -> NodeState:
        """Test line of sight from enemy to player.

        Uses the pre-computed has_los from the controller when available,
        falling back to raycast against all walls otherwise.

        Args:
            context: Behavior tree context containing 'enemy', 'has_los'.

        Returns:
            SUCCESS if player is visible, FAILURE otherwise.
        """
        has_los = context.get("has_los")
        if has_los is not None:
            return NodeState.SUCCESS if has_los else NodeState.FAILURE

        from systems.raycast import raycast

        enemy = context["enemy"]
        player_rect = context["player_rect"]

        dx = player_rect.centerx - enemy.x
        dy = player_rect.centery - enemy.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > enemy.genome.vision:
            return NodeState.FAILURE

        walls = [w.rect for w in context["level"].walls]
        if raycast((enemy.x, enemy.y), (player_rect.centerx, player_rect.centery), walls):
            context["has_los"] = True
            return NodeState.SUCCESS

        context["has_los"] = False
        return NodeState.FAILURE


class HasPursuitTarget(BTNode):
    """Condition node that checks if the enemy has an active pursuit target.

    The pursuit timer is set when the enemy last saw the player and decays
    at a rate scaled by the hearing gene. Higher hearing = longer pursuit.
    """

    def _tick(self, context: dict) -> NodeState:
        """Check whether pursuit is still active.

        Args:
            context: Behavior tree context containing 'pursuit_timer'.

        Returns:
            SUCCESS if pursuit timer > 0, FAILURE otherwise.
        """
        if context.get("pursuit_timer", 0.0) > 0.0:
            return NodeState.SUCCESS
        return NodeState.FAILURE


class InvestigateLocation(BTNode):
    """Action node that sends the enemy to the last known player position."""

    def _tick(self, context: dict) -> NodeState:
        """Move to last known player location.

        Args:
            context: Behavior tree context containing 'enemy' and 'player_x/y'.

        Returns:
            RUNNING while moving, SUCCESS when arrived.
        """
        enemy = context["enemy"]
        target_x = context.get("player_x", enemy.x)
        target_y = context.get("player_y", enemy.y)
        dt = context.get("dt", 0.016)

        enemy.set_patrol_target(target_x, target_y)

        dx = target_x - enemy.x
        dy = target_y - enemy.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < enemy.ARRIVAL_THRESHOLD:
            return NodeState.SUCCESS

        move_x = (dx / dist) * enemy.speed * dt
        move_y = (dy / dist) * enemy.speed * dt
        move_with_collision(enemy, move_x, move_y, context["level"])
        return NodeState.RUNNING
