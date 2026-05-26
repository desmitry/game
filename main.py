from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_FPS
from controllers.game_controller import GameController
from states.main_menu_state import MainMenuState

DISPLAY_FLAGS = pygame.DOUBLEBUF


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


def _blit_scaled(dst: pygame.Surface, src: pygame.Surface) -> tuple[int, int, float]:
    """Blit src onto dst preserving aspect ratio with black bars.

    Args:
        dst: Target surface.
        src: Source surface to blit.

    Returns:
        Tuple of (viewport_x, viewport_y, scale) for mouse unprojection.
    """
    dw, dh = dst.get_size()
    sw, sh = src.get_size()

    if dw == sw and dh == sh:
        dst.blit(src, (0, 0))
        return (0, 0, 1.0)

    scale = min(dw / sw, dh / sh)
    vw = int(sw * scale)
    vh = int(sh * scale)
    vx = (dw - vw) // 2
    vy = (dh - vh) // 2

    dst.fill((0, 0, 0))
    scaled = pygame.transform.scale(src, (vw, vh))
    dst.blit(scaled, (vx, vy))

    return (vx, vy, scale)


def _dispatch_event(
    event: pygame.event.Event,
    state: MainMenuState | GameController,
    game_surface: pygame.Surface,
) -> MainMenuState | GameController:
    """Dispatch a Pygame event to the current state.

    Args:
        event: Incoming Pygame event.
        state: Current game state.
        game_surface: Surface to render onto.

    Returns:
        The (possibly new) state after handling the event.
    """
    if isinstance(state, MainMenuState):
        result = state.handle_event(event)
        if result == "playing":
            return GameController(game_surface)
    elif isinstance(state, GameController):
        state.handle_event(event)
    return state


def _tick_state(
    dt: float,
    state: MainMenuState | GameController,
    game_surface: pygame.Surface,
) -> MainMenuState | GameController:
    """Update and draw one frame of the current state.

    Args:
        dt: Delta time in seconds.
        state: Current game state.
        game_surface: Surface to render onto.

    Returns:
        The (possibly new) state after the frame.
    """
    if isinstance(state, MainMenuState):
        state.update(dt)
        state.draw(game_surface)
    elif isinstance(state, GameController):
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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                fullscreen = not fullscreen
                window_surface = _toggle_fullscreen(fullscreen=fullscreen)
            state = _dispatch_event(event, state, game_surface)

        state = _tick_state(dt, state, game_surface)
        vx, vy, vs = _blit_scaled(window_surface, game_surface)
        if isinstance(state, GameController):
            state.viewport_x = vx
            state.viewport_y = vy
            state.viewport_scale = vs
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
