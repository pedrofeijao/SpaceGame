from constants import WIDTH, HEIGHT
import pygame
pygame.init()
# Set the dimensions of the window
pygame.display.set_caption("Spaceship Simulation")


window_size = (WIDTH, HEIGHT)
window = pygame.display.set_mode(window_size)

status_font = pygame.font.Font('assets/fonts/Grand9K Pixel.ttf', 24)
title_font = pygame.font.Font('assets/fonts/Grand9K Pixel.ttf', 64)
