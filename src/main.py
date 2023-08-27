import sys

import pygame

from init import window
from basegame import Game
from constants import GameState, FPS

pygame.time.set_timer(9998, 45000) # planet


if __name__ == "__main__":
    game = Game(window)
    dt = 0.0

    # image = scale_and_rotate('assets/Sprites/Ships/spaceShips_004.png', (200, 200), -90)
    # enemy = SineShip(image, speed_x=-1, acceleration=0.02, acceleration_switch=80)

    while game.state() != GameState.QUIT:

        game.manage_game_state(dt)
        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        dt = game.clock.tick(FPS) / 1000.0  # Divide by 1000.0 to get dt (time_passed) in seconds

    # Quit Pygame
    pygame.quit()
    sys.exit()
