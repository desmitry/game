from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_FPS


def main() -> None:
    """Run the game with state machine (menu, playing, paused)."""
    pygame.init()
    flags = pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF
    window_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Eclipsed Evolution")
    clock = pygame.time.Clock()

    from controllers.game_controller import GameController
    from states.main_menu_state import MainMenuState

    state: MainMenuState | GameController = MainMenuState()
    running = True

    while running:
        dt = clock.tick(TARGET_FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if isinstance(state, MainMenuState):
                result = state.handle_event(event)
                if result == "playing":
                    state = GameController(game_surface)
            elif isinstance(state, GameController):
                state.handle_event(event)

        if isinstance(state, MainMenuState):
            state.update(dt)
            state.draw(game_surface)
            window_surface.blit(game_surface, (0, 0))
            pygame.display.flip()
        elif isinstance(state, GameController):
            state.tick(dt)
            state.draw(game_surface)
            window_surface.blit(game_surface, (0, 0))
            pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
