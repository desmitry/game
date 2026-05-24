from __future__ import annotations

import random


class Genome:
    """Represents an enemy's genetic makeup with evolvable traits."""

    MIN_SPEED = 80.0
    MAX_SPEED = 180.0
    MIN_VISION = 120.0
    MAX_VISION = 320.0
    MIN_HEARING = 60.0
    MAX_HEARING = 280.0
    MIN_LIGHT_SENS = 0.2
    MAX_LIGHT_SENS = 1.8

    def __init__(
        self,
        speed: float = 100.0,
        vision: float = 200.0,
        hearing: float = 150.0,
        light_sensitivity: float = 1.0,
    ) -> None:
        """Initialize genome with trait values.

        Args:
            speed: Movement speed in pixels per second.
            vision: Vision cone range in pixels.
            hearing: Sound detection radius in pixels.
            light_sensitivity: How much the enemy is attracted to light.
        """
        self.speed = self._clamp(speed, self.MIN_SPEED, self.MAX_SPEED)
        self.vision = self._clamp(vision, self.MIN_VISION, self.MAX_VISION)
        self.hearing = self._clamp(hearing, self.MIN_HEARING, self.MAX_HEARING)
        self.light_sensitivity = self._clamp(
            light_sensitivity, self.MIN_LIGHT_SENS, self.MAX_LIGHT_SENS
        )

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        """Constrain value within bounds.

        Args:
            value: Input value.
            low: Minimum bound.
            high: Maximum bound.

        Returns:
            Clamped value.
        """
        return max(low, min(high, value))

    def as_dict(self) -> dict[str, float]:
        """Export genome as a serializable dictionary.

        Returns:
            Dict mapping trait names to values.
        """
        return {
            "speed": self.speed,
            "vision": self.vision,
            "hearing": self.hearing,
            "light_sensitivity": self.light_sensitivity,
        }

    @classmethod
    def random(cls) -> Genome:
        """Create a genome with randomized traits."""
        return cls(
            speed=random.uniform(cls.MIN_SPEED, cls.MAX_SPEED),  # noqa: S311
            vision=random.uniform(cls.MIN_VISION, cls.MAX_VISION),  # noqa: S311
            hearing=random.uniform(cls.MIN_HEARING, cls.MAX_HEARING),  # noqa: S311
            light_sensitivity=random.uniform(  # noqa: S311
                cls.MIN_LIGHT_SENS, cls.MAX_LIGHT_SENS
            ),
        )

    def crossover(self, other: Genome) -> tuple[Genome, Genome]:
        """Perform single-point crossover with another genome.

        Args:
            other: Mating partner genome.

        Returns:
            Tuple of two child genomes.
        """
        traits = list(self.as_dict().keys())
        point = len(traits) // 2

        a_traits = {}
        b_traits = {}
        for i, name in enumerate(traits):
            self_val = getattr(self, name)
            other_val = getattr(other, name)
            if i < point:
                a_traits[name] = self_val
                b_traits[name] = other_val
            else:
                a_traits[name] = other_val
                b_traits[name] = self_val

        return (
            Genome(**a_traits),
            Genome(**b_traits),
        )

    def mutate(self, rate: float = 0.1, amount: float = 0.2) -> None:
        """Apply random mutations to traits.

        Args:
            rate: Probability per trait of mutation.
            amount: Maximum fractional change applied to mutated traits.
        """
        bounds = {
            "speed": (self.MIN_SPEED, self.MAX_SPEED),
            "vision": (self.MIN_VISION, self.MAX_VISION),
            "hearing": (self.MIN_HEARING, self.MAX_HEARING),
            "light_sensitivity": (self.MIN_LIGHT_SENS, self.MAX_LIGHT_SENS),
        }
        for name, (low, high) in bounds.items():
            if random.random() < rate:  # noqa: S311
                current = getattr(self, name)
                delta = current * random.uniform(-amount, amount)  # noqa: S311
                setattr(self, name, self._clamp(current + delta, low, high))
