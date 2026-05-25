from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class GameState:
    """Base class for game states (menu, playing, paused)."""

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Process a single pygame event and optionally return a state transition.

        Args:
            event: Pygame event to process.

        Returns:
            Name of the next state to switch to, or None to stay.
        """
        raise NotImplementedError

    def update(self, dt: float) -> str | None:
        """Run per-frame logic for this state.

        Args:
            dt: Delta time in seconds.

        Returns:
            Name of the next state to switch to, or None to stay.
        """
        raise NotImplementedError

    def draw(self, screen: pygame.Surface) -> None:
        """Render the state to the screen.

        Args:
            screen: Pygame display surface to draw onto.
        """
        raise NotImplementedError
