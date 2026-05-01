class Health:
    """Tracks hit points and damage state for an entity."""

    def __init__(self, max_hp: int = 100) -> None:
        """Initialize health with maximum hit points.

        Args:
            max_hp: Maximum health value.
        """
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.is_dead = False

    def take_damage(self, amount: float) -> bool:
        """Apply damage and return whether the entity died.

        Args:
            amount: Damage value to subtract.

        Returns:
            True if the entity's health dropped to zero or below.
        """
        self.current_hp = max(0.0, self.current_hp - amount)
        if self.current_hp <= 0:
            self.is_dead = True
            return True
        return False

    def heal(self, amount: float) -> None:
        """Restore health up to the maximum.

        Args:
            amount: Health value to add.
        """
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        self.is_dead = False

    @property
    def ratio(self) -> float:
        """Current health as a fraction of maximum."""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
