import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame import Rect


def raycast(
    start: tuple[float, float],
    end: tuple[float, float],
    obstacles: list[Rect],
    step_size: float = 4.0,
) -> bool:
    """Check if a line of sight exists between two points.

    Args:
        start: Origin (x, y) coordinate.
        end: Target (x, y) coordinate.
        obstacles: List of blocking rectangles.
        step_size: Sampling interval along the ray.

    Returns:
        True if the ray reaches the target without hitting an obstacle.
    """
    start_x, start_y = start
    end_x, end_y = end
    dx = end_x - start_x
    dy = end_y - start_y
    length = math.sqrt(dx * dx + dy * dy)

    if length < 1.0:
        return True

    steps = int(length / step_size) + 1
    step_x = dx / steps
    step_y = dy / steps

    x = start_x
    y = start_y

    for _ in range(steps):
        x += step_x
        y += step_y

        for obstacle in obstacles:
            if obstacle.collidepoint(x, y):
                return False

    return True
