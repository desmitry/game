from __future__ import annotations

import random

import pygame  # noqa: TC002

from game.ai.bt_node import BTNode, NodeState


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
            RUNNING while moving, SUCCESS when target is reached.
        """
        enemy = context["enemy"]
        if enemy.is_patrolling:
            return NodeState.RUNNING
        return NodeState.SUCCESS


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

        Args:
            context: Behavior tree context containing 'enemy', 'player_rect', 'walls'.

        Returns:
            SUCCESS if player is visible, FAILURE otherwise.
        """
        from game.systems.raycast import raycast

        enemy = context["enemy"]
        player_rect: pygame.Rect = context["player_rect"]
        walls: list[pygame.Rect] = context.get("walls", [])

        dx = player_rect.centerx - enemy.x
        dy = player_rect.centery - enemy.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > enemy.VISION_RADIUS:
            return NodeState.FAILURE

        if raycast((enemy.x, enemy.y), (player_rect.centerx, player_rect.centery), walls):
            context["has_los"] = True
            return NodeState.SUCCESS

        context["has_los"] = False
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

        enemy.set_patrol_target(target_x, target_y)

        dx = target_x - enemy.x
        dy = target_y - enemy.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < enemy.ARRIVAL_THRESHOLD:
            return NodeState.SUCCESS
        return NodeState.RUNNING
