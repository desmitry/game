from __future__ import annotations

import json
import random
from pathlib import Path

from systems.genome import Genome

POPULATION_SIZE = 6
ELITE_COUNT = 2
MUTATION_RATE = 0.12
MUTATION_AMOUNT = 0.2


class GeneticAlgorithm:
    """Manages enemy evolution across generations using a genetic algorithm."""

    def __init__(self) -> None:
        """Initialize GA with a starting population."""
        self.generation = 0
        self.population: list[Genome] = [Genome.random() for _ in range(POPULATION_SIZE)]
        self._fitness: list[float] = [0.0] * POPULATION_SIZE
        self._tracked_enemies: dict[int, float] = {}

    def reset_population(self) -> None:
        """Create a fresh random population for a new game."""
        self.population = [Genome.random() for _ in range(POPULATION_SIZE)]
        self._fitness = [0.0] * POPULATION_SIZE

    def record_damage(self, enemy_id: int, amount: float) -> None:
        """Track damage dealt by a specific enemy.

        Args:
            enemy_id: Unique enemy identifier.
            amount: Damage value to add.
        """
        self._tracked_enemies[enemy_id] = self._tracked_enemies.get(enemy_id, 0.0) + amount

    def record_tracking_time(self, enemy_id: int, dt: float) -> None:
        """Track how long an enemy has been chasing the player.

        Args:
            enemy_id: Unique enemy identifier.
            dt: Delta time to add.
        """
        self._tracked_enemies[enemy_id] = self._tracked_enemies.get(enemy_id, 0.0) + dt * 10.0

    def calculate_fitness(self) -> None:
        """Score each enemy based on performance and update population fitness."""
        for enemy_id, score in self._tracked_enemies.items():
            if enemy_id < len(self._fitness):
                self._fitness[enemy_id] = score
        self._tracked_enemies.clear()

    def evolve(self) -> list[Genome]:
        """Breed the next generation using selection, crossover, and mutation.

        Returns:
            New population of evolved genomes.
        """
        self.calculate_fitness()

        ranked = sorted(
            range(len(self.population)),
            key=lambda i: self._fitness[i],
            reverse=True,
        )

        next_gen: list[Genome] = []

        # Keep elite individuals unchanged
        for i in range(min(ELITE_COUNT, len(ranked))):
            idx = ranked[i]
            genome = self.population[idx]
            next_gen.append(
                Genome(genome.speed, genome.vision, genome.hearing, genome.light_sensitivity)
            )

        # Fill rest via crossover and mutation
        while len(next_gen) < POPULATION_SIZE:
            parent_a = self._select_parent(ranked)
            parent_b = self._select_parent(ranked)
            child_a, child_b = parent_a.crossover(parent_b)
            child_a.mutate(MUTATION_RATE, MUTATION_AMOUNT)
            child_b.mutate(MUTATION_RATE, MUTATION_AMOUNT)
            next_gen.append(child_a)
            if len(next_gen) < POPULATION_SIZE:
                next_gen.append(child_b)

        self.population = next_gen
        self._fitness = [0.0] * POPULATION_SIZE
        self.generation += 1

        return self.population

    def _select_parent(self, ranked: list[int]) -> Genome:
        """Select a parent using tournament selection.

        Args:
            ranked: Indices sorted by fitness descending.

        Returns:
            Selected genome.
        """
        tournament_size = 3
        best = None
        best_score = -1.0
        for _ in range(tournament_size):
            idx = random.choice(ranked[: len(ranked) // 2 + 1])  # noqa: S311
            if self._fitness[idx] > best_score:
                best_score = self._fitness[idx]
                best = idx
        return self.population[best or 0]

    def save(self, filepath: str) -> None:
        """Persist GA state to a JSON file.

        Args:
            filepath: Path to save file.
        """
        data = {
            "generation": self.generation,
            "population": [g.as_dict() for g in self.population],
        }
        with Path(filepath).open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> bool:
        """Restore GA state from a JSON file.

        Args:
            filepath: Path to save file.

        Returns:
            True if the file was loaded successfully.
        """
        path = Path(filepath)
        if not path.exists():
            return False

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.generation = data.get("generation", 0)
        self.population = [Genome(**g) for g in data.get("population", [])]
        self._fitness = [0.0] * len(self.population)
        return True
