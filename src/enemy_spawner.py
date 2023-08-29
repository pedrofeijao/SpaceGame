import math
import random

import pygame

from src.constants import WIDTH, HEIGHT, EnemySpawnEvent
from src.enemies import Swarmer, Asteroid, ASTEROID_SIZE, SlashBullet, FireBullet, SineShip, SimpleBullet, RoundBullet
from src.utils import unit_vector


class EnemySpawner:
    def __init__(self, game):
        self.game = game

        # Sprite groups
        self.enemy_ships = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.all_enemies = pygame.sprite.Group()

    def add_enemy_ship_sprite(self, ship):
        self.enemy_ships.add(ship)
        self.all_enemies.add(ship)

    def add_enemy_projectile_sprite(self, projectile):
        self.enemy_projectiles.add(projectile)
        self.all_enemies.add(projectile)

    def spawn_swarmer(self):
        swarmer = Swarmer(WIDTH + 20, random.randint(0, HEIGHT), self.game.spaceship)
        self.add_enemy_ship_sprite(swarmer)

    def spawn_asteroid(self):
        for idx in range(10):  # try a few times to get an asteroid without collision with existing ones
            asteroid = Asteroid(WIDTH, random.randint(100, HEIGHT - 100))
            if pygame.sprite.spritecollide(asteroid, self.enemy_ships, False):
                asteroid.kill()
            else:
                self.add_enemy_ship_sprite(asteroid)
                break

    def spawn_smaller_asteroids(self, asteroid):
        direction = 1 if random.random() > 0.5 else -1
        new_size = asteroid.size - 1
        speed_mult = math.sqrt(4.0 - new_size)
        offset = ASTEROID_SIZE * new_size / 3
        ast1 = Asteroid(asteroid.x - direction * offset, asteroid.y - offset, size=asteroid.size - 1,
                        speed_x=-speed_mult * direction * (0.5 + random.random()),
                        speed_y=-speed_mult * (0.5 + random.random()))
        ast2 = Asteroid(asteroid.x + direction * offset, asteroid.y + offset, size=asteroid.size - 1,
                        speed_x=speed_mult * direction * (0.5 + random.random()),
                        speed_y=speed_mult * (0.5 + random.random()))
        self.add_enemy_ship_sprite(ast1)
        self.add_enemy_ship_sprite(ast2)

    def spawn_random_slash_bullet(self):
        bullet = SlashBullet(self.game.spaceship, WIDTH + 10, random.randint(40, HEIGHT - 40))
        self.add_enemy_projectile_sprite(bullet)

    def spawn_random_fire_bullet(self):
        bullet = FireBullet(WIDTH + 10, random.randint(40, HEIGHT - 40))
        self.add_enemy_projectile_sprite(bullet)

    def spawn_random_sineship(self, shoot_time=1, group=1):
        y = random.randint(100, HEIGHT - 100)
        for idx in range(group):
            ship = SineShip(self, x=WIDTH + 75 * idx, y=y, shoot_time=shoot_time, first_shot_delay=idx * 0.2,
                            kill_offset=100*group)
            self.add_enemy_ship_sprite(ship)

    def spawn_simple_bullet(self, x, y, **kwargs):
        bullet = SimpleBullet(x, y, **kwargs)
        self.add_enemy_projectile_sprite(bullet)

    def spawn_targeted_round_bullet(self, x, y, speed=4, **kwargs):
        target_vector = unit_vector(x, y, self.game.spaceship.x, self.game.spaceship.y)
        bullet = RoundBullet(x, y, speed_x=speed * target_vector[0], speed_y=speed * target_vector[1])
        self.add_enemy_projectile_sprite(bullet)

    def check_spawn_events(self, event):

        if event.type == EnemySpawnEvent.ASTEROID.value:
            self.spawn_asteroid()

        if event.type == EnemySpawnEvent.SWARM.value:
            self.spawn_swarmer(**event.dict)

        if event.type == EnemySpawnEvent.FIREBALL.value:
            self.spawn_random_fire_bullet(**event.dict)

        if event.type == EnemySpawnEvent.SLASHBULLET.value:
            self.spawn_random_slash_bullet(**event.dict)

        if event.type == EnemySpawnEvent.SINESHIP.value:
            self.spawn_random_sineship(**event.dict)
