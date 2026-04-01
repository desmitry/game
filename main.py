def main() -> None:
    """Initialize and run the game controller."""
    from game.controllers.game_controller import GameController

    controller = GameController()
    controller.run()


if __name__ == "__main__":
    main()
