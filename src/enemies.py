import math
import random

import numpy as np
import pygame

from constants import FPS, WIDTH, HEIGHT
from flying_obj import FlyingObject, FlyingObjectFragile, AnimatedFOF
from utils import SpriteSheet, scale_and_rotate, unit_vector

CHASER_SHIP_IMG = "assets/Sprites/Ships/spaceShips_007.png"
FIRE_BULLET_IMG = "assets/Sprites/Fire/3/Fire-Wrath__1{}.png"
SLASH_BULLET_IMG = "assets/Sprites/Slash/Alternative 3/1/Alternative_3_0{}.png"
ASTEROID_IMG = "assets/Sprites/Meteors/meteorBrown_big{}.png"
SWARMER_IMG = "assets/Sprites/Ships/BadShips.png"


class Swarmer(FlyingObject):
    def __init__(self, x, y, target, speed=3, health=1, size=1):
        self.sprite_sheet_image = pygame.image.load(SWARMER_IMG).convert_alpha()
        self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
        frames = [self.sprite_sheet.get_image(idx, 3, width=16, height=16, scale=2) for idx in range(12, 20)] + \
                 [self.sprite_sheet.get_image(idx, 4, width=16, height=16, scale=2) for idx in range(20)] + \
                 [self.sprite_sheet.get_image(idx, 5, width=16, height=16, scale=2) for idx in range(20)] + \
                 [self.sprite_sheet.get_image(idx, 6, width=16, height=16, scale=2) for idx in range(20)] + \
                 [self.sprite_sheet.get_image(idx, 7, width=16, height=16, scale=2) for idx in range(5)]
        self.frames = {angle: frame for angle, frame in zip(np.arange(0, 360, 5), frames)}
        image = self.frames[0]
        super().__init__(image, x, y, health=health, size=size, collision_damage=10)
        self.target = target
        self.speed = speed
        self.score = 5

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


class Asteroid(FlyingObjectFragile):
    pixel_size = 40

    def __init__(self, x, y, size=3, speed_x=0.0, speed_y=0.0):
        angle = random.randint(0, 359)
        image_idx = random.randint(1, 4)
        image = scale_and_rotate(
            ASTEROID_IMG.format(image_idx),
            (Asteroid.pixel_size * size, Asteroid.pixel_size * size),
            angle)
        speed_x = speed_x or -3 * random.random() - 1
        speed_y = speed_y or 2 - 4 * random.random()
        super().__init__(image, x, y, speed_x, speed_y, size=size, health=size, collision_damage=size * 10)
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
    def __init__(self, target, x, y, speed_x=-2.5, speed_y=0.0, accel_x=-0, damage=25):
        super().__init__(fire_img, 5, x, y, speed_x, speed_y, accel_x=accel_x, collision_damage=damage)
        self.score = 0
        self.target = target


class SineShip(FlyingObject):
    def __init__(self, image, x=WIDTH, y=HEIGHT / 2, speed_x=-6, speed_y=0, acceleration=0.3, acceleration_switch=20):
        super().__init__(image, x, y, speed_x=speed_x, speed_y=speed_y)
        self.acceleration = acceleration
        self.acceleration_switch = acceleration_switch
        self.acceleration_timer = self.acceleration_switch

    def update(self):
        super().update()
        self.speed_y += self.acceleration
        self.acceleration_timer -= 1
        if self.acceleration_timer <= 0:
            self.acceleration_timer = self.acceleration_switch * 2
            self.acceleration *= -1
