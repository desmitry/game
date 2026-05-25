from __future__ import annotations

import pygame

from states.game_state import GameState
from systems.text_renderer import TextRenderer

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BLINK_INTERVAL = 0.5


class MainMenuState(GameState):
    """Title screen with start prompt."""

    def __init__(self) -> None:
        """Initialize menu with title font."""
        self._text = TextRenderer()
        self._blink_timer = 0.0
        self._show_prompt = True

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Start the game on ENTER key press.

        Args:
            event: Pygame event to process.

        Returns:
            'playing' if ENTER pressed, None otherwise.
        """
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "playing"
        return None

    def update(self, dt: float) -> str | None:
        """Blink the prompt text every half-second.

        Args:
            dt: Delta time in seconds.

        Returns:
            None (no state transition from timing alone).
        """
        self._blink_timer += dt
        if self._blink_timer > BLINK_INTERVAL:
            self._blink_timer = 0.0
            self._show_prompt = not self._show_prompt
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Render the title screen.

        Args:
            screen: Pygame display surface to draw onto.
        """
        screen.fill((5, 5, 10))

        title = self._text.render("Eclipsed Evolution", 72, (180, 180, 200))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        screen.blit(title, title_rect)

        sub = self._text.render("A Top-Down 2D Stealth Survival Game", 32, (100, 100, 120))
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(sub, sub_rect)

        lines = [
            "You are a scavenger trapped in an abandoned,",
            "completely dark subterranean research facility.",
            "Survive by managing light sources and avoiding",
            "biological anomalies that hunt you.",
            "",
            "Every floor, enemies evolve to counter your tactics.",
        ]
        y_offset = SCREEN_HEIGHT // 2 + 10
        for line in lines:
            text = self._text.render(line, 22, (120, 120, 130))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 28

        if self._show_prompt:
            prompt = self._text.render("Press ENTER to start", 32, (150, 150, 150))
            prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 20))
            screen.blit(prompt, prompt_rect)
