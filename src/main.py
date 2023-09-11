import sys

import pygame

from src.basegame import Game
from src.constants import GameState, FPS

if __name__ == "__main__":
    game = Game()
    dt = 0.0

    while game.state() != GameState.QUIT:
        game.manage_game_state(dt)
        # Update the display
        pygame.display.flip()

        # if game.state_manager.game_state == GameState.RUNNING:
        dt = game.clock.tick(FPS) / 1000.0  # Divide by 1000.0 to get dt (time_passed) in seconds

    # Quit Pygame
    pygame.quit()
    sys.exit()
