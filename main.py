from __future__ import annotations

import pygame

TARGET_FPS = 60


def main() -> None:
    """Run the game with state machine (menu, playing, paused)."""
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Eclipsed Evolution")
    clock = pygame.time.Clock()

    from game.controllers.game_controller import GameController
    from game.states.main_menu_state import MainMenuState

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
                    state = GameController()
            elif isinstance(state, GameController):
                state.handle_event(event)

        if isinstance(state, MainMenuState):
            state.update(dt)
            state.draw(screen)
        elif isinstance(state, GameController):
            state.tick(dt)
            state.draw(screen)

    pygame.quit()


if __name__ == "__main__":
    main()
