import math
import random

import numpy as np
import pygame

from src.constants import FPS, WIDTH, HEIGHT
from src.flying_obj import FlyingObject, FlyingObjectFragile, AnimatedFOF
from src.utils import SpriteSheet, scale_and_rotate, unit_vector

CHASER_SHIP_IMG = "assets/Sprites/Ships/spaceShips_007.png"
FIRE_BULLET_IMG = "assets/Sprites/Fire/3/Fire-Wrath__1{}.png"
SLASH_BULLET_IMG = "assets/Sprites/Slash/Alternative 3/1/Alternative_3_0{}.png"
ASTEROID_IMG = "assets/Sprites/Meteors/meteorBrown_big{}.png"
SWARMER_IMG = "assets/Sprites/Ships/BadShips.png"

swarm_sprite_sheet = SpriteSheet(pygame.image.load(SWARMER_IMG).convert_alpha())
swarm_frames = [swarm_sprite_sheet.get_image(idx, 3, width=16, height=16, scale=2) for idx in range(12, 20)] + \
               [swarm_sprite_sheet.get_image(idx, 4, width=16, height=16, scale=2) for idx in range(20)] + \
               [swarm_sprite_sheet.get_image(idx, 5, width=16, height=16, scale=2) for idx in range(20)] + \
               [swarm_sprite_sheet.get_image(idx, 6, width=16, height=16, scale=2) for idx in range(20)] + \
               [swarm_sprite_sheet.get_image(idx, 7, width=16, height=16, scale=2) for idx in range(5)]


sineship_image = scale_and_rotate('assets/Sprites/Enemies/enemyBlack1.png', (93 / 2, 84 / 2), -90)
SIMPLE_BULLET_IMG = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserRed02.png", (10, 25), -90)

round_bullet_sheet = SpriteSheet(pygame.image.load("assets/Sprites/Laser Sprites/round_bullet.png").convert_alpha())
round_bullet_frames = [round_bullet_sheet.get_image(idx, 0, width=16, height=19, scale=2) for idx in [0, 1, 2, 1]]

class Swarmer(FlyingObject):
    def __init__(self, x, y, target, speed=3, health=1, size=1):
        self.frames = {angle: frame for angle, frame in zip(np.arange(0, 360, 5), swarm_frames)}
        image = self.frames[0]
        super().__init__(image, x, y, health=health, size=size, collision_damage=10)
        self.target = target
        self.speed = speed
        self.score = 10

    def update(self):
        delta_x = self.target.x - self.x
        delta_y = self.target.y - self.y
        factor = self.speed / math.sqrt(delta_x ** 2 + delta_y ** 2)
        self.speed_x = factor * delta_x
        self.speed_y = factor * delta_y
        self.update_positon()
        # Image angle:
        angle = (math.degrees(math.atan2(delta_y, delta_x)) // 5 * 5 + 90) % 360
        self.image = self.frames[angle]


ASTEROID_ANGLES = np.arange(0, 350, 30)
ASTEROID_SIZE = 40
asteroid_images = {(image_idx, size, angle): scale_and_rotate(
    ASTEROID_IMG.format(image_idx),
    (ASTEROID_SIZE * size, ASTEROID_SIZE * size),
    angle) for image_idx in [1, 2, 3, 4] for size in [1, 2, 3] for angle in ASTEROID_ANGLES
}


class Asteroid(FlyingObjectFragile):

    def __init__(self, x, y, size=3, speed_x=0.0, speed_y=0.0):
        angle = random.choice(ASTEROID_ANGLES)
        image_idx = random.randint(1, 4)
        speed_x = speed_x or -3 * random.random() - 1
        speed_y = speed_y or 2 - 4 * random.random()
        super().__init__(asteroid_images[image_idx, size, angle], x, y, speed_x, speed_y, size=size, health=size,
                         collision_damage=size * 10)
        self.score = 10 * (4 - size)

    def __str__(self):
        return f"A {self.rect.x, self.rect.y, self.speed_x, self.speed_y}"


class ChaserShip(FlyingObject):
    def __init__(self, game, x, y, chase_trigger=5, chase_time=2, inertia=0.5):
        image = scale_and_rotate(CHASER_SHIP_IMG, (90, 90), -90)
        super().__init__(image, x, y, speed_x=-0.5)
        self.move_trigger = FPS * chase_trigger
        self.move_counter = self.move_trigger
        self.game = game
        self.inertia = inertia
        self.chase_time = chase_time

    def update(self):
        super().update()
        self.move_counter -= 1
        if self.move_counter == 0:
            self.move_counter = self.move_trigger
            dx = self.game.spaceship.x - self.x
            dy = self.game.spaceship.y - self.y
            magnitude = math.sqrt(dx ** 2 + dy ** 2)
            self.speed_x = self.inertia * dx / magnitude
            self.speed_y = self.inertia * dy / magnitude
            self.game.sprite_moves.add_absolute_move(self, target_x=self.game.spaceship.x,
                                                     target_y=self.game.spaceship.y, time=self.chase_time)


slash_img = [scale_and_rotate(SLASH_BULLET_IMG.format(idx)) for idx in [1, 2, 3, 4, 5]]


class SlashBullet(AnimatedFOF):
    def __init__(self, target, x, y, speed_x=-1.5, speed_y=0.0, accel_x=-0.1, damage=25):
        super().__init__(slash_img, 4, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage)
        self.score = 0
        self.target = target

    def update(self):
        if self.x > self.target.x:
            self.accel_x, self.accel_y = unit_vector(self.x, self.y, self.target.x, self.target.y, scale=0.25)
            self.accel_x = min(self.accel_x, 0)
            if self.speed_x < -5:
                self.speed_x = -5
            if self.speed_y > 5:
                self.speed_y = 5
            if self.speed_y < -5:
                self.speed_y = -5
        else:
            self.accel_y = self.accel_x = 0
        super().update()


fire_img = [scale_and_rotate(FIRE_BULLET_IMG.format(idx), (140, 140)) for idx in [1, 2, 3, 4, 5, 4, 3, 2]]


class FireBullet(AnimatedFOF):
    def __init__(self, x, y, speed_x=-2.5, speed_y=0.0, accel_x=-0, damage=25):
        super().__init__(fire_img, 5, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage)
        self.score = 0




class RoundBullet(AnimatedFOF):
    def __init__(self, x, y, speed_x=-3, speed_y=0.0, accel_x=-0, damage=10):
        super().__init__(round_bullet_frames, 8, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage)
        self.score = 0

class SimpleBullet(FlyingObjectFragile):
    def __init__(self, x, y, speed_x=-8.0, speed_y=0.0, damage=15):
        super().__init__(SIMPLE_BULLET_IMG, x, y, speed_x, speed_y, collision_damage=damage, size=1)
        self.score = 0


class SineShip(FlyingObjectFragile):
    def __init__(self, enemy_spawner, x=WIDTH, y=HEIGHT / 2, speed_x=-3, speed_y=0, acceleration=0.2,
                 acceleration_switch=30, shoot_time=2, first_shot_delay=0, kill_offset=200):
        super().__init__(sineship_image, x, y, speed_x=speed_x, speed_y=speed_y,
                         health=5, kill_offset=kill_offset,
                         hit_color=(255, 30, 30, 100), size=2)
        self.enemy_spawner = enemy_spawner
        self.acceleration = acceleration
        self.acceleration_switch = acceleration_switch
        self.acceleration_timer = self.acceleration_switch
        self.score = 100
        self.shoot_time = FPS * shoot_time
        self.shoot_time_count = self.shoot_time * (1 + first_shot_delay)

    def update(self):
        super().update()
        self.speed_y += self.acceleration
        self.acceleration_timer -= 1
        if self.acceleration_timer <= 0:
            self.acceleration_timer = self.acceleration_switch * 2
            self.acceleration *= -1

        # Shoot
        if self.shoot_time > 0:
            if self.shoot_time_count <= 0:
                self.shoot()
                self.shoot_time_count = self.shoot_time
            else:
                self.shoot_time_count -= 1

    def shoot(self):
        # self.enemy_spawner.spawn_simple_bullet(self.rect.left, self.y)
        self.enemy_spawner.spawn_targeted_round_bullet(self.rect.left, self.y)


class Gem(FlyingObjectFragile):
    def __init__(self, x, y, size=1, speed_x=-0.5, speed_y=0.0):
        image = scale_and_rotate(
            ASTEROID_IMG.format(image_idx),
            (Asteroid.pixel_size * size, Asteroid.pixel_size * size),
            angle)
        super().__init__(image, x, y, speed_x, speed_y, size=size, health=size, collision_damage=0)
        self.score = 10 * (4 - size)
