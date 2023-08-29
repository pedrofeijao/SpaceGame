import sys

import pygame

from src.init import window
from src.basegame import Game
from src.constants import GameState, FPS

pygame.time.set_timer(9998, 45000) # planet


if __name__ == "__main__":
    game = Game(window)
    dt = 0.0


    while game.state() != GameState.QUIT:

        game.manage_game_state(dt)
        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        dt = game.clock.tick(FPS) / 1000.0  # Divide by 1000.0 to get dt (time_passed) in seconds

    # Quit Pygame
    pygame.quit()
    sys.exit()
