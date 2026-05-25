from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_FPS
from controllers.game_controller import GameController
from states.main_menu_state import MainMenuState

DISPLAY_FLAGS = pygame.SCALED | pygame.DOUBLEBUF


def _toggle_fullscreen(*, fullscreen: bool) -> pygame.Surface:
    """Switch between windowed and fullscreen mode.

    Args:
        fullscreen: True to enter fullscreen, False for windowed.

    Returns:
        The new display surface (recreated with new mode).
    """
    if fullscreen:
        info = pygame.display.Info()
        w = info.current_w
        h = info.current_h
        return pygame.display.set_mode((w, h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    return pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DISPLAY_FLAGS)


def _blit_scaled(
    dst: pygame.Surface, src: pygame.Surface, offset: tuple[int, int] = (0, 0)
) -> None:
    """Blit src onto dst, scaling src if sizes differ.

    Args:
        dst: Target surface.
        src: Source surface to blit.
        offset: Top-left position for the blit (default (0,0)).
    """
    if dst.get_size() == src.get_size():
        dst.blit(src, offset)
    else:
        pygame.transform.scale(src, dst.get_size(), dst)


def _dispatch_event(
    event: pygame.event.Event,
    state: MainMenuState | GameController,
    game_surface: pygame.Surface,
    mouse_scale_x: float = 1.0,
    mouse_scale_y: float = 1.0,
) -> MainMenuState | GameController:
    """Dispatch a Pygame event to the current state.

    Args:
        event: Incoming Pygame event.
        state: Current game state.
        game_surface: Surface to render onto.
        mouse_scale_x: Screen-to-game horizontal scale.
        mouse_scale_y: Screen-to-game vertical scale.

    Returns:
        The (possibly new) state after handling the event.
    """
    if isinstance(state, MainMenuState):
        result = state.handle_event(event)
        if result == "playing":
            return GameController(game_surface, mouse_scale_x, mouse_scale_y)
    elif isinstance(state, GameController):
        state.handle_event(event)
    return state


def _tick_state(
    dt: float,
    state: MainMenuState | GameController,
    game_surface: pygame.Surface,
    mouse_scale_x: float = 1.0,
    mouse_scale_y: float = 1.0,
) -> MainMenuState | GameController:
    """Update and draw one frame of the current state.

    Args:
        dt: Delta time in seconds.
        state: Current game state.
        game_surface: Surface to render onto.
        mouse_scale_x: Screen-to-game horizontal scale.
        mouse_scale_y: Screen-to-game vertical scale.

    Returns:
        The (possibly new) state after the frame.
    """
    if isinstance(state, MainMenuState):
        state.update(dt)
        state.draw(game_surface)
    elif isinstance(state, GameController):
        state.mouse_scale_x = mouse_scale_x
        state.mouse_scale_y = mouse_scale_y
        state.tick(dt)
        state.draw(game_surface)
        if not state.running:
            return MainMenuState()
    return state


def main() -> None:
    """Run the game with state machine (menu, playing, paused)."""
    pygame.init()
    window_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DISPLAY_FLAGS)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Eclipsed Evolution")
    clock = pygame.time.Clock()
    fullscreen = False

    state: MainMenuState | GameController = MainMenuState()
    running = True

    while running:
        dt = clock.tick(TARGET_FPS) / 1000.0

        win_w, win_h = window_surface.get_size()
        mouse_scale_x = SCREEN_WIDTH / win_w
        mouse_scale_y = SCREEN_HEIGHT / win_h

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                fullscreen = not fullscreen
                window_surface = _toggle_fullscreen(fullscreen=fullscreen)
            state = _dispatch_event(event, state, game_surface, mouse_scale_x, mouse_scale_y)

        state = _tick_state(dt, state, game_surface, mouse_scale_x, mouse_scale_y)
        _blit_scaled(window_surface, game_surface)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
