from enum import Enum
import pygame

WIDTH, HEIGHT = 1400, 900

FPS = 60


class GameState(Enum):
    START_SCREEN, GAME_OVER, RUNNING, PAUSED, UPGRADE, QUIT = range(6)


SHIELD_INITIAL_DAMAGE = 20

BG_SPEED = 1

STATUS_BAR_HEIGHT = 50

# Events

NEXT_LEVEL_EVENT = 9990


class EnemySpawnEvent(Enum):
    SWARM = pygame.event.Event(9991)
    ASTEROID = pygame.event.Event(9992)
    FIREBALL = pygame.event.Event(9993)
    SLASHBULLET = pygame.event.Event(9994)
    SINESHIP = pygame.event.Event(9995)
