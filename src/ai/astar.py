from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.pathfinding_grid import PathfindingGrid

NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
CARDINAL_COST = 1.0


def astar(
    grid: PathfindingGrid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """Find the shortest path between two tile coordinates using A*.

    Args:
        grid: PathfindingGrid containing obstacle data.
        start: Starting tile (tile_x, tile_y).
        goal: Destination tile (tile_x, tile_y).

    Returns:
        Ordered list of tile coordinates from start to goal,
        or an empty list if no path exists.
    """
    start_tx, start_ty = start
    goal_tx, goal_ty = goal

    if not grid.is_valid(start_tx, start_ty):
        return []
    if not grid.is_valid(goal_tx, goal_ty):
        return []

    open_set: list[tuple[float, int, tuple[int, int]]] = []
    counter = 0
    heapq.heappush(open_set, (0, counter, start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    g_score: dict[tuple[int, int], float] = {start: 0.0}

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current == goal:
            return _reconstruct_path(came_from, current)

        cx, cy = current

        for dx, dy in NEIGHBORS:
            neighbor = (cx + dx, cy + dy)
            if not grid.is_valid(*neighbor):
                continue

            tentative_g = g_score[current] + CARDINAL_COST

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h = _heuristic(neighbor, goal)
                counter += 1
                heapq.heappush(open_set, (tentative_g + h, counter, neighbor))

    return []


def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Manhattan distance heuristic for 4-directional movement.

    Args:
        a: First tile coordinate.
        b: Second tile coordinate.

    Returns:
        Estimated movement cost between the two tiles.
    """
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return CARDINAL_COST * (dx + dy)


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int]],
    current: tuple[int, int],
) -> list[tuple[int, int]]:
    """Build the final path by backtracking from goal to start.

    Args:
        came_from: Mapping of each tile to its predecessor.
        current: Goal tile coordinate.

    Returns:
        List of tiles from start to goal inclusive.
    """
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path
