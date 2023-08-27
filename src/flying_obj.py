import math
import random

import pygame

from utils import scale_and_rotate, SpriteSheet
from constants import HEIGHT, WIDTH


class FlyingObject(pygame.sprite.Sprite):
    def __init__(self, image, x, y, speed_x=0.0, speed_y=0.0, accel_x=0.0, accel_y=0.0,
                 health=1, size=1, collision_damage=10, hit_color=(255, 255, 255, 50)):
        super().__init__()
        self.original_image = image
        self.image = image
        self.mask = pygame.mask.from_surface(self.image, threshold=20)
        # Copy original image and add an transparent mask on top for the hit:
        self.hit_image = image.copy()
        self.hit_image.blit(self.mask.to_surface(setcolor=hit_color, unsetcolor=None).convert_alpha(), (0, 0))

        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.center = round(self.x), round(self.y)
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.accel_x = accel_x
        self.accel_y = accel_y
        self.hit_cooldown = 0
        self.hit_cooldown_time = 8
        self.health = health
        self.size = size
        self.collision_damage = collision_damage

    def hit_animation(self):
        self.hit_cooldown = self.hit_cooldown_time

    def update_positon(self):
        self.speed_x += self.accel_x
        self.speed_y += self.accel_y
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.center = round(self.x), round(self.y)

    def update_hit_image(self):
        if self.hit_cooldown > 0:
            self.image = self.hit_image
        else:
            self.image = self.original_image
        self.hit_cooldown -= 1

    def update(self):
        self.update_positon()
        self.update_hit_image()

    def got_hit(self, damage=1):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        self.hit_animation()
        return False

    def ship_collide(self, spaceship):
        spaceship.health -= self.collision_damage
        destroyed = self.got_hit(damage=spaceship.collision_damage)

        # adjust speeds
        factor = 1 / math.sqrt(self.size)
        space_x = min(2.0, spaceship.speed_x)
        space_y = min(2.0, spaceship.speed_y)
        self.speed_x, spaceship.speed_x = factor * space_x, (1 / factor) * self.speed_x
        self.speed_y, spaceship.speed_y = factor * space_y, (1 / factor) * self.speed_y

        return destroyed


class FlyingObjectFragile(FlyingObject):

    def __init__(self, *args, offset=50, **kwargs):
        self.offset = offset
        super().__init__(*args, **kwargs)

    def update(self):
        super().update()
        self.check_bounds()

    def check_bounds(self):
        if self.rect.bottom < -self.offset \
                or self.rect.top > HEIGHT + self.offset \
                or self.rect.right < -self.offset \
                or self.rect.left > WIDTH + self.offset:
            self.kill()


class AnimatedFOF(FlyingObjectFragile):
    def __init__(self, images, anim_speed, *args, offset=50, **kwargs):
        super().__init__(images[0], *args, offset=offset, **kwargs)
        self.images = images
        self.img_idx = 0
        self.anim_speed = anim_speed
        self.anim_speed_counter = 0

    def update(self):
        FlyingObject.update_positon(self)
        super().check_bounds()
        self.anim_speed_counter += 1
        if self.anim_speed_counter > self.anim_speed:
            self.anim_speed_counter = 0
            self.img_idx = (self.img_idx + 1) % len(self.images)
            self.image = self.images[self.img_idx]


class Planet(FlyingObjectFragile):
    def __init__(self):

        self.size = random.randint(200, 500)
        if random.random() > 0.5:
            y = random.randint(round(-self.size / 4), 0)
        else:
            y = random.randint(HEIGHT, HEIGHT + round(self.size / 4))

        model = random.randint(1, 16)
        rotation = random.randint(0, 360)
        image = scale_and_rotate(f"assets/Sprites/Planets/planet-{model}.png", (self.size, self.size), rotation)
        super().__init__(image, WIDTH + self.size / 2, y, speed_x=-1.2, offset=self.size)


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite_sheet, n_frames, width, height, scale=4, frame_update_steps=5):
        super().__init__()
        # self.sprite_sheet_image = pygame.image.load('assets/explosion.png').convert_alpha()
        # self.sprite_sheet_image = pygame.image.load('assets/explosion1.png').convert_alpha()

        self.sprite_sheet_image = pygame.image.load(sprite_sheet).convert_alpha()
        self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
        self.active_frame = 0
        self.frame_timer = 0
        self.frame_update_steps = frame_update_steps
        self.frames = []
        for idx in range(n_frames):
            self.frames.append(self.sprite_sheet.get_image(idx, 0, width=width, height=height, scale=scale))

        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.audio = pygame.mixer.Sound('assets/explosion.wav')
        self.audio.set_volume(0.25)
        self.audio.play()

    @staticmethod
    def create(x, y, size=1):
        EXPLOSIONS = [
            ['assets/explosion.png', 6, 32, 32, 1, 4],
            ['assets/explosion1.png', 9, 15, 14, 2.13, 3],
            ['assets/explosion2.png', 9, 10, 9, 3.2, 3],
        ]
        exp_param = random.choice(EXPLOSIONS)
        exp_param[-2] *= size
        return Explosion(x, y, *exp_param)

    def update(self):
        self.frame_timer += 1
        if self.frame_timer >= self.frame_update_steps:
            self.active_frame += 1
            self.frame_timer = 0
            if self.active_frame >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.active_frame]
                self.rect = self.image.get_rect(center=self.rect.center)

