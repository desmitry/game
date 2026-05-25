from __future__ import annotations

from ai.bt_node import BTNode, NodeState


class Sequence(BTNode):
    """Composite node that succeeds only if all children succeed."""

    def __init__(self, children: list[BTNode]) -> None:
        """Initialize sequence with child nodes.

        Args:
            children: Ordered list of child nodes to tick.
        """
        self.children = children

    def _tick(self, context: dict) -> NodeState:
        """Tick each child in order until one fails or all succeed.

        Args:
            context: Shared behavior tree context.

        Returns:
            SUCCESS if all children succeed, FAILURE if any fails,
            or RUNNING if the current child is still running.
        """
        for child in self.children:
            result = child.tick(context)
            if result != NodeState.SUCCESS:
                return result
        return NodeState.SUCCESS


class Selector(BTNode):
    """Composite node that succeeds if any child succeeds."""

    def __init__(self, children: list[BTNode]) -> None:
        """Initialize selector with child nodes.

        Args:
            children: Ordered list of child nodes to tick.
        """
        self.children = children

    def _tick(self, context: dict) -> NodeState:
        """Tick each child in order until one succeeds or all fail.

        Args:
            context: Shared behavior tree context.

        Returns:
            SUCCESS if any child succeeds, FAILURE if all fail,
            or RUNNING if the current child is still running.
        """
        for child in self.children:
            result = child.tick(context)
            if result != NodeState.FAILURE:
                return result
        return NodeState.FAILURE
