from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class ObjectPool[T]:
    """Pre-allocates and recycles game entities to avoid GC stutters."""

    def __init__(
        self,
        factory: Callable[[], T],
        reset: Callable[[T], None],
        size: int = 50,
    ) -> None:
        """Initialize pool with a factory and reset function.

        Args:
            factory: Callable that creates a new entity instance.
            reset: Callable that resets an entity to its default state.
            size: Number of pre-allocated entities.
        """
        self._factory = factory
        self._reset = reset
        self._available: list[T] = [factory() for _ in range(size)]
        self._in_use: list[T] = []

    def acquire(self) -> T | None:
        """Obtain an entity from the pool.

        Returns:
            A recycled entity, or None if the pool is exhausted.
        """
        if not self._available:
            return None

        entity = self._available.pop()
        self._in_use.append(entity)
        return entity

    def release(self, entity: T) -> None:
        """Return a used entity back to the pool.

        Args:
            entity: Entity to recycle.
        """
        self._reset(entity)
        if entity in self._in_use:
            self._in_use.remove(entity)
            self._available.append(entity)

    def release_all(self) -> None:
        """Return all in-use entities to the available pool."""
        for entity in self._in_use:
            self._reset(entity)
        self._available.extend(self._in_use)
        self._in_use.clear()

    @property
    def active(self) -> list[T]:
        """Return currently in-use entities."""
        return list(self._in_use)

    def resize(self, new_size: int) -> None:
        """Adjust pool capacity, creating or discarding entities as needed.

        Args:
            new_size: Target total pool capacity.
        """
        total = len(self._available) + len(self._in_use)
        if new_size > total:
            for _ in range(new_size - total):
                self._available.append(self._factory())
        elif new_size < total:
            while len(self._available) + len(self._in_use) > new_size:
                if self._available:
                    self._available.pop()
                elif self._in_use:
                    self._in_use.pop()
