from __future__ import annotations

import enum
from abc import ABC, abstractmethod


class NodeState(enum.Enum):
    """Possible states for a behavior tree node tick result."""

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BTNode(ABC):
    """Abstract base class for all behavior tree nodes."""

    def tick(self, context: dict) -> NodeState:
        """Execute the node logic with the given context.

        Args:
            context: Shared data dictionary for the behavior tree.

        Returns:
            NodeState indicating success, failure, or running.
        """
        return self._tick(context)

    @abstractmethod
    def _tick(self, context: dict) -> NodeState:
        """Implement node-specific logic.

        Args:
            context: Shared data dictionary for the behavior tree.

        Returns:
            NodeState indicating success, failure, or running.
        """
