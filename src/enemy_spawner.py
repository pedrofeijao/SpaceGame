import math
import random

import numpy as np
import pygame

from src.constants import EnemySpawnEvent
from src.enemies import Swarmer, Asteroid, SlashBullet, FireBullet, SineShip, SimpleBullet, RoundBullet, Gem, \
    ChaserShip, SpreadBulletBoss
from src.utils import unit_vector, SpriteSheet, scale_and_rotate

CHASER_SHIP_IMG = "assets/Sprites/Ships/spaceShips_007.png"
SPREAD_BOSS_IMG = "assets/Sprites/Enemies/enemyGreen4.png"
FIRE_BULLET_IMG = "assets/Sprites/Fire/3/Fire-Wrath__1{}.png"
SLASH_BULLET_IMG = "assets/Sprites/Slash/Alternative 3/1/Alternative_3_0{}.png"
ASTEROID_IMG = "assets/Sprites/Meteors/meteorBrown_big{}.png"
GEM_IMG = "assets/Sprites/Gems/{:02}.png"
SWARMER_IMG = "assets/Sprites/Ships/BadShips.png"
ASTEROID_ANGLES = np.arange(0, 350, 30)
ASTEROID_SIZE = 0.5


class EnemySpawner:
    def __init__(self, game):
        self.game = game
        self.images = EnemyImages()
        # Sprite groups
        self.enemy_ships = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.all_enemies = pygame.sprite.Group()
        self.gems = pygame.sprite.Group()

    def add_enemy_ship_sprite(self, ship):
        self.enemy_ships.add(ship)
        self.all_enemies.add(ship)

    def add_enemy_projectile_sprite(self, projectile):
        self.enemy_projectiles.add(projectile)
        self.all_enemies.add(projectile)

    def add_gem(self, gem):
        self.gems.add(gem)

    def spawn_swarmer(self, x, y):
        swarmer = Swarmer(self.images.swarm_frames, x, y, self.game.spaceship)
        self.add_enemy_ship_sprite(swarmer)

    def spawn_chasership(self, x, y):
        ship = ChaserShip(self.game.spaceship, self.images.chasership_image, x, y)
        self.game.sprite_moves.add_absolute_move(ship, target_x=x-300,
                                                 target_y=y, time=1)
        self.add_enemy_ship_sprite(ship)

    def spawn_spread_bullet_boss(self, **kwargs):
        x = self.game.width - self.images.chasership_image.get_width() - 300
        y = self.game.height // 2
        x_radius = 100
        y_radius = 200
        ship = SpreadBulletBoss(self.images.spread_boss, x, y,
                            x_radius=x_radius, y_radius=y_radius, angle_speed=0.2, score=1000, **kwargs)
        self.game.sprite_moves.add_anchored_offset(ship, target_x=500, target_y=0, time=2)
        self.add_enemy_ship_sprite(ship)

    def spawn_asteroid(self):
        size = random.randint(2, 3)
        for idx in range(10):  # try a few times to get an asteroid without collision with existing ones
            asteroid = Asteroid(self.images.asteroid_images, ASTEROID_ANGLES, self.game.width,
                                random.randint(100, self.game.height - 100), size=size)
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
        ast1 = Asteroid(self.images.asteroid_images, ASTEROID_ANGLES, asteroid.x - direction * offset, asteroid.y - offset, size=asteroid.size - 1,
                        speed_x=-speed_mult * direction * (random.random()),
                        speed_y=-speed_mult * (random.random()))
        ast2 = Asteroid(self.images.asteroid_images, ASTEROID_ANGLES, asteroid.x + direction * offset, asteroid.y + offset, size=asteroid.size - 1,
                        speed_x=speed_mult * direction * (random.random()),
                        speed_y=speed_mult * (random.random()))
        self.add_enemy_ship_sprite(ast1)
        self.add_enemy_ship_sprite(ast2)

    def spawn_random_slash_bullet(self):
        bullet = SlashBullet(self.images.slash_img, self.game.spaceship, self.game.width + 10, random.randint(40, self.game.height - 40))
        self.add_enemy_projectile_sprite(bullet)

    def spawn_random_fire_bullet(self):
        bullet = FireBullet(self.images.fire_img, self.game.width + 10, random.randint(40, self.game.height - 40))
        self.add_enemy_projectile_sprite(bullet)

    def spawn_random_sineship(self, shoot_time=1, group=1, level=1):
        y = random.randint(100, self.game.height - 100)
        for idx in range(group):
            ship = SineShip(self.images.sineship_image, x=self.game.width + 75 * idx, y=y, shoot_time=shoot_time,
                            kill_offset=100 * group, level=level)
            self.add_enemy_ship_sprite(ship)

    def spawn_simple_bullet(self, x, y, **kwargs):
        bullet = SimpleBullet(self.images.simple_bullet_img, x, y, **kwargs)
        self.add_enemy_projectile_sprite(bullet)

    def spawn_targeted_round_bullet(self, x, y, speed=6, **kwargs):
        target_vector = unit_vector(x, y, self.game.spaceship.x, self.game.spaceship.y)
        bullet = RoundBullet(self.images.round_bullet_frames, x, y,
                             speed_x=speed * target_vector[0], speed_y=speed * target_vector[1], **kwargs)
        self.add_enemy_projectile_sprite(bullet)

    def spawn_angled_round_bullet(self, x, y, angle, speed=6, **kwargs):
        target_x = math.cos(math.radians(angle))
        target_y = math.sin(math.radians(angle))
        bullet = RoundBullet(self.images.round_bullet_frames, x, y, speed_x=speed * target_x, speed_y=speed * target_y)
        self.add_enemy_projectile_sprite(bullet)

    def spawn_gem(self, x, y, level=1, n_gems=1):
        if n_gems == 1:
            angles = [0]
        else:
            angles = np.arange(360, step=360/n_gems) + 90
        for angle in angles:
            speed_x = 4 * math.cos(math.radians(angle))
            speed_y = 4 * math.sin(math.radians(angle))
            gem = Gem(self.images.gem_images[level], frame_wait=20, spaceship=self.game.spaceship, x=x, y=y,
                      speed_x=speed_x, speed_y=speed_y, level=level)
            self.add_gem(gem)

    def check_spawn_events(self, event):
        match event.type:
            case EnemySpawnEvent.ASTEROID.value:
                self.spawn_asteroid()

            case EnemySpawnEvent.SWARM.value:
                self.spawn_swarmer(self.game.width + 20, random.randint(0, self.game.height), **event.dict)

            case EnemySpawnEvent.FIREBALL.value:
                self.spawn_random_fire_bullet(**event.dict)

            case EnemySpawnEvent.SLASHBULLET.value:
                self.spawn_random_slash_bullet(**event.dict)

            case EnemySpawnEvent.SINESHIP.value:
                self.spawn_random_sineship(**event.dict)

            case EnemySpawnEvent.CHASERSHIP.value:
                self.spawn_chasership(self.game.width + 100, random.randint(0, self.game.height), **event.dict)

            case EnemySpawnEvent.SPREADBOSS.value:
                self.spawn_spread_bullet_boss(**event.dict)




class EnemyImages():
    def __init__(self):
        swarm_sprite_sheet = SpriteSheet(pygame.image.load(SWARMER_IMG).convert_alpha())

        self.swarm_frames = [swarm_sprite_sheet.get_image(idx, 3, width=16, height=16, scale=2) for idx in range(12, 20)] + \
                       [swarm_sprite_sheet.get_image(idx, 4, width=16, height=16, scale=2) for idx in range(20)] + \
                       [swarm_sprite_sheet.get_image(idx, 5, width=16, height=16, scale=2) for idx in range(20)] + \
                       [swarm_sprite_sheet.get_image(idx, 6, width=16, height=16, scale=2) for idx in range(20)] + \
                       [swarm_sprite_sheet.get_image(idx, 7, width=16, height=16, scale=2) for idx in range(5)]

        self.chasership_image = scale_and_rotate(CHASER_SHIP_IMG, scale_by=1, rotate=90)
        self.sineship_image = scale_and_rotate('assets/Sprites/Enemies/enemyBlack1.png', scale_by=0.5, rotate=-90)
        self.simple_bullet_img = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserRed02.png", rotate=-90)
        self.spread_boss = scale_and_rotate(SPREAD_BOSS_IMG, scale_by=2, rotate=-90)

        round_bullet_sheet = SpriteSheet(
            pygame.image.load("assets/Sprites/Laser Sprites/round_bullet.png").convert_alpha())
        self.round_bullet_frames = [round_bullet_sheet.get_image(idx, 0, width=16, height=19, scale=2) for idx in
                               [0, 1, 2, 1]]

        self.fire_img = [scale_and_rotate(FIRE_BULLET_IMG.format(idx), scale_by=1) for idx in [1, 2, 3, 4, 5, 4, 3, 2]]

        self.asteroid_images = {(image_idx, size, angle): scale_and_rotate(
            ASTEROID_IMG.format(image_idx),
            size * ASTEROID_SIZE,
            angle) for image_idx in [1, 2, 3, 4] for size in [1, 2, 3] for angle in ASTEROID_ANGLES
        }
        self.slash_img = [scale_and_rotate(SLASH_BULLET_IMG.format(idx)) for idx in [1, 2, 3, 4, 5]]

        self.gem_images = {
            1: [scale_and_rotate(GEM_IMG.format(idx), scale_by=0.4) for idx in [3, 11]],
            2: [scale_and_rotate(GEM_IMG.format(idx), scale_by=0.4) for idx in [2, 10]],
            3: [scale_and_rotate(GEM_IMG.format(idx), scale_by=0.4) for idx in [7, 15]],
        }

