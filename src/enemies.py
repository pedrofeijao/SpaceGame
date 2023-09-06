import math
import random

import numpy as np
import pygame

from src.constants import FPS
from src.flying_obj import FlyingObject, AnimatedFO
from src.utils import SpriteSheet, scale_and_rotate, unit_vector


class Swarmer(FlyingObject):
    def __init__(self, swarm_frames, x, y, target, speed=4, health=1, size=1):
        self.frames = {angle: frame for angle, frame in zip(np.arange(0, 360, 5), swarm_frames)}
        image = self.frames[0]
        super().__init__(image, x, y, health=health, size=size, collision_damage=10)
        self.target = target
        self.speed = speed
        self.score = 10
        self.max_angle = 359
        self.min_angle = 181

    def update(self):
        delta_x = self.target.x - self.x
        delta_y = self.target.y - self.y
        factor = self.speed / math.sqrt(delta_x ** 2 + delta_y ** 2)
        self.speed_x = factor * delta_x
        self.speed_y = factor * delta_y
        self.update_positon()
        # Image angle:
        angle = (math.degrees(math.atan2(self.speed_y, self.speed_x)) // 5 * 5 + 90) % 360
        self.image = self.frames[angle]


class Asteroid(FlyingObject):

    def __init__(self, asteroid_images, angles, x, y, size=3, speed_x=0.0, speed_y=0.0):
        angle = random.choice(angles)
        image_idx = random.randint(1, 4)
        speed_x = speed_x or -3 * random.random() - 2
        speed_y = speed_y or 1 - 2 * random.random()
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


class SlashBullet(AnimatedFO):
    def __init__(self, slash_img, target, x, y, speed_x=-1.5, speed_y=0.0, accel_x=-0.1, damage=25, max_speed=6):
        super().__init__(slash_img, 4, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage)
        self.score = 0
        self.target = target
        self.max_speed = max_speed

    def update(self):
        if self.x > self.target.x:
            self.accel_x, self.accel_y = unit_vector(self.x, self.y, self.target.x, self.target.y, scale=0.5)
            self.accel_x = min(self.accel_x, 0)
            if abs(self.speed_x) > self.max_speed:
                self.speed_x = self.max_speed * np.sign(self.speed_x)
            if abs(self.speed_y) > self.max_speed:
                self.speed_y = self.max_speed * np.sign(self.speed_y)
        else:
            self.accel_y = self.accel_x = 0
        super().update()


class FireBullet(AnimatedFO):
    def __init__(self, fire_img, x, y, speed_x=-2.5, speed_y=0.0, accel_x=-0, damage=25):
        super().__init__(fire_img, 5, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage,
                         size=3, mask_image_idx=3)
        self.score = 0


class RoundBullet(AnimatedFO):
    def __init__(self, round_bullet_frames, x, y, speed_x=-3, speed_y=0.0, accel_x=-0, damage=10):
        super().__init__(round_bullet_frames, 8, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage)
        self.score = 0


class SimpleBullet(FlyingObject):
    def __init__(self, simple_bullet_img, x, y, speed_x=-8.0, speed_y=0.0, damage=15):
        super().__init__(simple_bullet_img, x, y, speed_x, speed_y, collision_damage=damage, size=1)
        self.score = 0


class SineShip(FlyingObject):
    def __init__(self, enemy_spawner, sineship_image, x=0, y=0, speed_x=-3, speed_y=0, acceleration=0.2,
                 acceleration_switch=30, shoot_time=2, first_shot_delay=0, kill_offset=200, level=1):
        super().__init__(sineship_image, x, y, speed_x=speed_x, speed_y=speed_y,
                         health=5, kill_offset=kill_offset,
                         hit_color=(255, 30, 30, 100), size=2)
        self.enemy_spawner = enemy_spawner
        self.acceleration = acceleration
        self.acceleration_switch = acceleration_switch
        self.acceleration_timer = self.acceleration_switch
        self.score = 100 * level
        self.shoot_time = FPS * shoot_time
        self.shoot_time_count = self.shoot_time * (1 + first_shot_delay)
        self.level = level

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
        if self.level == 1:
            self.enemy_spawner.spawn_simple_bullet(self.rect.left, self.y)
        elif self.level == 2:
            self.enemy_spawner.spawn_targeted_round_bullet(self.rect.left, self.y)
        else:
            raise (NotImplemented("No shoot for level 3+ sineship."))


class Gem(AnimatedFO):
    def __init__(self, gem_images, frame_wait, spaceship, x, y, level=1):
        super().__init__(gem_images, frame_wait, x, y)
        self.level = level
        self.is_following = False
        self.follow_speed = 6
        self.speed_x = -1
        self.spaceship = spaceship
        self.score = 20 * 5 ** (level-1)

    def update(self):
        if self.is_following:
            self.speed_x, self.speed_y = unit_vector(self.x, self.y, self.spaceship.x, self.spaceship.y,
                                                     scale=self.follow_speed)
        else:
            if abs(self.x - self.spaceship.x) + abs(
                    self.y - self.spaceship.y) <= self.spaceship.gem_auto_pickup_distance:
                self.is_following = True
        super().update()
