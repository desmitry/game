from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from pygame.mixer import Sound


def _init_pygame_mixer() -> pygame.mixer | None:
    """Try to import and initialise pygame.mixer, returning the module or None."""
    try:
        import pygame.mixer as _mixer

        _mixer.init()
    except ImportError, ModuleNotFoundError:
        return None
    else:
        return _mixer


class SoundManager:
    """Manages sound effects and music playback with volume control."""

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize the sound manager and mixer.

        Args:
            base_path: Directory containing sound assets. Defaults to
                       <package_dir>/audio/.
        """
        if base_path:
            self._base = Path(base_path)
        else:
            self._base = Path(__file__).parent

        self._mixer_mod = _init_pygame_mixer()
        self._available = self._mixer_mod is not None
        self._sfx: dict[str, Sound] = {}
        self._music_volume = 0.5
        self._sfx_volume = 0.7
        self._ambient_playing = False

    def load_sfx(self, name: str, filename: str) -> None:
        """Load a sound effect from file.

        Args:
            name: Identifier to reference the sound later.
            filename: Relative filename within the audio directory.
        """
        if not self._available:
            return
        path = self._base / filename
        if path.exists():
            with suppress(pygame.error):
                sound = self._mixer_mod.Sound(str(path))  # type: ignore[union-attr]
                sound.set_volume(self._sfx_volume)
                self._sfx[name] = sound

    def play_sfx(self, name: str) -> None:
        """Play a loaded sound effect.

        Args:
            name: Identifier of the sound to play.
        """
        sound = self._sfx.get(name)
        if sound:
            sound.play()

    def play_ambient(self, filename: str, loops: int = -1) -> None:
        """Start background music or ambient track.

        Args:
            filename: Relative path to the music file.
            loops: Number of loops (-1 for infinite).
        """
        if not self._available:
            return
        path = self._base / filename
        if path.exists():
            with suppress(pygame.error):
                self._mixer_mod.music.load(str(path))  # type: ignore[union-attr]
                self._mixer_mod.music.set_volume(self._music_volume)  # type: ignore[union-attr]
                self._mixer_mod.music.play(loops=loops)  # type: ignore[union-attr]
                self._ambient_playing = True

    def stop_ambient(self) -> None:
        """Stop the currently playing music."""
        if not self._available:
            return
        self._mixer_mod.music.stop()  # type: ignore[union-attr]
        self._ambient_playing = False

    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0).

        Args:
            volume: Volume level.
        """
        if not self._available:
            return
        self._music_volume = max(0.0, min(1.0, volume))
        self._mixer_mod.music.set_volume(self._music_volume)  # type: ignore[union-attr]

    @property
    def music_volume(self) -> float:
        """Current music volume (0.0 to 1.0)."""
        return self._music_volume

    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume (0.0 to 1.0).

        Args:
            volume: Volume level.
        """
        self._sfx_volume = max(0.0, min(1.0, volume))
        for sound in self._sfx.values():
            sound.set_volume(self._sfx_volume)

    def cleanup(self) -> None:
        """Stop all sounds and quit the mixer."""
        if not self._available:
            return
        self.stop_ambient()
        for sound in self._sfx.values():
            sound.stop()
        with suppress(pygame.error):
            self._mixer_mod.quit()  # type: ignore[union-attr]
