from __future__ import annotations

from systems.genetic_algorithm import POPULATION_SIZE, GeneticAlgorithm
from systems.genome import Genome


class TestGenome:
    """Tests for Genome crossover logic."""

    def test_crossover_produces_two_offspring(self) -> None:
        """Crossover returns exactly two child genomes."""
        a = Genome(speed=100, vision=200, hearing=150, light_sensitivity=1.0)
        b = Genome(speed=180, vision=300, hearing=250, light_sensitivity=1.8)
        c1, c2 = a.crossover(b)
        assert isinstance(c1, Genome)
        assert isinstance(c2, Genome)

    def test_crossover_mixes_traits(self) -> None:
        """Children inherit traits from both parents."""
        a = Genome(speed=100, vision=200, hearing=150, light_sensitivity=1.0)
        b = Genome(speed=180, vision=300, hearing=250, light_sensitivity=1.8)
        c1, c2 = a.crossover(b)
        all_speeds = {c1.speed, c2.speed}
        assert 100 in all_speeds or 180 in all_speeds

    def test_mutation_changes_values(self) -> None:
        """Mutation alters trait values."""
        g = Genome(speed=140, vision=250, hearing=200, light_sensitivity=1.5)
        original = g.speed
        for _ in range(100):
            g.mutate(rate=1.0, amount=0.1)
        assert g.speed != original

    def test_mutation_stays_in_bounds(self) -> None:
        """Mutation does not produce values outside min/max range."""
        g = Genome(speed=140, vision=250, hearing=200, light_sensitivity=1.5)
        for _ in range(50):
            g.mutate(rate=1.0, amount=1.0)
        assert Genome.MIN_SPEED <= g.speed <= Genome.MAX_SPEED
        assert Genome.MIN_VISION <= g.vision <= Genome.MAX_VISION
        assert Genome.MIN_HEARING <= g.hearing <= Genome.MAX_HEARING
        assert Genome.MIN_LIGHT_SENS <= g.light_sensitivity <= Genome.MAX_LIGHT_SENS


class TestGeneticAlgorithm:
    """Tests for GA population evolution."""

    def test_population_size_preserved(self) -> None:
        """Evolving maintains the population count."""
        ga = GeneticAlgorithm()
        ga.evolve()
        assert len(ga.population) == POPULATION_SIZE

    def test_generation_increments(self) -> None:
        """Each evolve call increments the generation counter."""
        ga = GeneticAlgorithm()
        assert ga.generation == 0
        ga.evolve()
        assert ga.generation == 1

    def test_fitness_tracking(self) -> None:
        """Recorded fitness values are reflected after calculate_fitness."""
        ga = GeneticAlgorithm()
        ga.record_damage(0, 50.0)
        ga.calculate_fitness()
        assert ga._fitness[0] > 0
