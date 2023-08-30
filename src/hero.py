from enum import Enum

import pygame
import math
from queue import Queue

import numpy as np

from src.constants import WIDTH, SHIELD_INITIAL_DAMAGE, FPS, HEIGHT, STATUS_BAR_HEIGHT

from src.utils import scale_and_rotate, SpriteSheet
from src.flying_obj import FlyingObject, FlyingObjectFragile, AnimatedFOF

ROTATING_SHIELD_IMG = 'assets/Sprites/Rocket parts/spaceRocketParts_015.png'
rotating_shield_img = scale_and_rotate(ROTATING_SHIELD_IMG, scale_by=0.8, rotate=90)

WINGMAN_IMG = 'assets/Sprites/Ships/spaceShips_002.png'
wingman_img = scale_and_rotate(WINGMAN_IMG, scale_by=0.3, rotate=90)

ROCKET_SPRITE_SHEET = "assets/Sprites/Missiles/projectile_rocket_16x16.png"

# PROJECTILE_IMGS = {
#     angle: scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue02.png", (13, 37), angle) for angle in range(361)
# }
PROJECTILE_IMGS = {
    angle: scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue06.png", 0.7, angle) for angle in range(361)
}


class Spaceship(FlyingObject):
    acceleration: float

    def __init__(self, x, y):
        image = scale_and_rotate('assets/Sprites/Ships/spaceShips_001.png', 0.5, 90)

        self.shadow = pygame.mask.from_surface(image).to_surface().convert_alpha()
        self.shadow.set_alpha(40)
        super().__init__(image, x, y, health=100, collision_damage=2, hit_color=(255, 0, 0, 100))

        self.acceleration = 0.4
        self.max_speed = 200
        self.brakes = 2
        self.hit_cooldown = 0
        self.hit_cooldown_time = 8
        self.health_bar = self.health

        self.pos_history = Queue()
        self.history_len = 6
        for i in range(self.history_len):
            self.pos_history.put((x, y))
        self.last_pos = self.pos_history.get()

        # self.thruster_images = {
        #     pygame.K_s: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', (14, 23)),
        #     pygame.K_w: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', (14, 23), 180),
        #     pygame.K_d: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', (14, 23), 90),
        #     pygame.K_a: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', (14, 23), -90)}

        self.thruster_images = {
            pygame.K_s: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png'),
            pygame.K_w: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', rotate=180),
            pygame.K_d: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', rotate=90),
            pygame.K_a: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', rotate=-90)}

        self.weapons = WeaponsController(self)

    def update(self):
        keys = self.apply_acceleration()

        # Health:
        if self.health > 100:
            self.health = 100
        if self.health < 0:
            self.health = 0

        if self.health < self.health_bar:
            self.health_bar -= 1
        if self.health > self.health_bar:
            self.health_bar += 1

        # max speed:
        self.check_max_speed()

        # Update the ship's position based on its velocity
        self.update_positon()

        self.check_border_hit()

        # Store position, get last:
        self.pos_history.put((self.x, self.y))
        self.last_pos = self.pos_history.get()

        # Wingmen/Shields
        self.weapons.update()

        # Image:
        super().update_hit_image()

    def check_border_hit(self):
        # Wrap the ship's position if it goes off the screen
        if self.rect.right >= WIDTH:
            self.x = WIDTH - self.rect.width / 2
            self.speed_x *= -0.25
        if self.rect.left < 0:
            self.x = self.rect.width / 2
            self.speed_x *= -0.25
        if self.rect.bottom >= HEIGHT:
            self.y = HEIGHT - self.rect.height / 2
            self.speed_y *= -0.25
        if self.rect.top < STATUS_BAR_HEIGHT:
            self.y = STATUS_BAR_HEIGHT + self.rect.height / 2
            self.speed_y *= -0.25
        self.rect.center = round(self.x), round(self.y)

    def apply_acceleration(self):
        keys = pygame.key.get_pressed()
        idle = True
        if keys[pygame.K_a]:
            idle = False
            if self.speed_x > 0:
                self.speed_x -= self.brakes * self.acceleration
            else:
                self.speed_x -= self.acceleration
        if keys[pygame.K_d]:
            idle = False
            if self.speed_x < 0:
                self.speed_x += self.brakes * self.acceleration
            else:
                self.speed_x += self.acceleration
        if keys[pygame.K_w]:
            idle = False
            if self.speed_y > 0:
                self.speed_y -= self.brakes * self.acceleration
            else:
                self.speed_y -= self.acceleration
        if keys[pygame.K_s]:
            idle = False
            if self.speed_y < 0:
                self.speed_y += self.brakes * self.acceleration
            else:
                self.speed_y += self.acceleration
        if idle:
            self.speed_x *= 0.98
            self.speed_y *= 0.98

        return keys

    def check_max_speed(self):
        if self.speed_x > self.max_speed:
            self.speed_x = self.max_speed
        if self.speed_y > self.max_speed:
            self.speed_y = self.max_speed
        if self.speed_x < -self.max_speed:
            self.speed_x = -self.max_speed
        if self.speed_y < -self.max_speed:
            self.speed_y = -self.max_speed

    def draw(self, draw_window):
        # Spaceship:
        draw_window.blit(self.shadow, self.shadow.get_rect(center=self.last_pos))
        draw_window.blit(self.image, self.rect.topleft)
        keys = pygame.key.get_pressed()

        # Thrusters:
        if keys[pygame.K_a]:
            draw_window.blit(self.thruster_images[pygame.K_a], (self.rect.x + self.rect.width, self.rect.y))
            draw_window.blit(self.thruster_images[pygame.K_a], (self.rect.x + self.rect.width, self.rect.y + 30))
        if keys[pygame.K_d]:
            draw_window.blit(self.thruster_images[pygame.K_d], (self.rect.x - 25, self.rect.y + 20))
        if keys[pygame.K_w]:
            draw_window.blit(self.thruster_images[pygame.K_w], (self.rect.x, self.rect.y + self.rect.height))
        if keys[pygame.K_s]:
            draw_window.blit(self.thruster_images[pygame.K_s], (self.rect.x, self.rect.y - 20))

        # Weapons:
        self.weapons.draw(draw_window)


missile_sprites = SpriteSheet(
    pygame.image.load(ROCKET_SPRITE_SHEET).convert_alpha())
missile_img = [missile_sprites.get_image(idx, 4, 16, 16, 3) for idx in [1, 2, 3]]


class Missile(AnimatedFOF):
    def __init__(self, x, y, speed_x=3.0, speed_y=0.0, accel_x=0.1, damage=3):
        super().__init__(missile_img, 4, x, y, speed_x, speed_y, accel_x=accel_x)
        self.damage = damage


class WingMan(FlyingObject):
    def __init__(self, x_offset, y_offset, spaceship, firing_speed=100):
        super().__init__(wingman_img, spaceship.x, spaceship.y, hit_color=(255, 0, 0, 100))
        self.spaceship = spaceship
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.firing_speed = firing_speed
        self.firing_cooldown = firing_speed

    def update(self):
        self.x = self.spaceship.last_pos[0] + self.x_offset
        self.y = self.spaceship.last_pos[1] + self.y_offset
        self.rect.center = round(self.x), round(self.y)

        # fire:
        self.firing_cooldown -= 1
        if self.firing_cooldown <= 0:
            self.firing_cooldown = self.firing_speed
            self.spaceship.weapons.wingman_fire(self.x, self.y)



    def __str__(self):
        return f"Wingman ({self.x}, {self.y})"


class RotatingShield(FlyingObject):
    def __init__(self, spaceship, angle, max_radius, health=20, radius_speed=1, rotation_speed=5):
        super().__init__(rotating_shield_img, spaceship.x, spaceship.y, health=health)
        self.spaceship = spaceship
        self.angle = angle
        self.current_radius = 0
        self.max_radius = max_radius
        self.radius_speed = radius_speed
        self.rotation_speed = rotation_speed
        self.damage = 5

    def update(self):
        if self.current_radius < self.max_radius:
            self.current_radius += self.radius_speed
        self.angle = (self.angle + self.rotation_speed) % 360
        self.x = self.spaceship.x + self.current_radius * math.cos(math.radians(self.angle))
        self.y = self.spaceship.y + self.current_radius * math.sin(math.radians(self.angle))
        self.rect.center = round(self.x), round(self.y)


class UpgradeController():
    def __init__(self, spaceship):
        self.spaceship = spaceship

        # Weapons:
        self.projectile_level = 1
        self.wingman_level = 0
        self.rotating_shield_level = 0
        self.mines_level = 0
        self.laser_level = 0
        self.pulse_beam_level = 0

        # Upgrades:
        self.shield_level = 0
        self.fire_rate_level = 0
        self.damage_level = 0
        self.projectile_size_level = 0
        self.speed_level = 0


class Projectile(FlyingObjectFragile):
    # projectile_img = [scale_and_rotate(f"assets/Sprites/Laser Sprites/{i:02d}.png", (40, 40)) for i in range(1, 11)]

    def __init__(self, x, y, speed_x=12.0, speed_y=0.0, angle=0, damage=1):
        # image = Projectile.projectile_img[random.randint(0, len(Projectile.projectile_img) - 1)]
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/01.png", (40, 40), -angle)
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/28.png", (105, 46), -angle)
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue06.png", (7, 19), 90 - angle)
        # print(round(-angle % 360))
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue02.png", (13, 37), -angle % 360)
        image = PROJECTILE_IMGS[round((90 - angle) % 360)]
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue01.png", (9, 54), 90 - angle)
        super().__init__(image, x, y, speed_x, speed_y)
        self.damage = damage


class Shield(FlyingObject):
    def __init__(self, spaceship):
        self.frames = {
            idx: scale_and_rotate(f"assets/Sprites/Effects/shield{idx}.png", 2, -90) for idx in [1, 2, 3]
        }
        self.frames[0] = pygame.Surface((0, 0)).convert_alpha()
        super().__init__(self.frames[1], 0, 0, collision_damage=SHIELD_INITIAL_DAMAGE)
        self.max_shield = 0
        self.current_shield = 0
        self.shield_recharge_time = 2 * FPS
        self.shield_recharge = self.shield_recharge_time
        self.spaceship = spaceship

    def increase_level(self):
        if self.max_shield < 3:
            self.max_shield += 1
            self.current_shield = self.max_shield
            self.shield_recharge = 0

    def update(self):
        if self.max_shield > self.current_shield:
            self.shield_recharge -= 1
            if self.shield_recharge <= 0:
                self.current_shield += 1
                self.shield_recharge = self.shield_recharge_time
        if self.current_shield > 0:
            self.image = self.frames[self.current_shield]
            self.x = self.spaceship.x
            self.y = self.spaceship.y
            self.rect.center = round(self.x + 10), round(self.y)



class WeaponsController:
    def __init__(self, spaceship):
        self.projectiles = pygame.sprite.Group()

        self.spaceship = spaceship
        self.fire_audio = pygame.mixer.Sound('assets/laserfire01.ogg')

        # Main weapon:
        self.fire_cooldown = 0
        self.fire_cooldown_time = FPS * 0.5
        self.spread = 30
        self.n_projectiles = 1
        self.bursts = 1
        self.current_burst = 1
        self.burst_cooldown_time = 3
        self.burst_cooldown = 0

        # Wingman
        self.wingmen = pygame.sprite.Group()
        self.wingman_pos = [(40, -120), (40, +120), (20, -70), (20, 70)]

        # Rotating shields
        self.rotating_shields = pygame.sprite.Group()

        # Shield:
        self.shield = Shield(self.spaceship)
        self.shield_group = pygame.sprite.Group()
        self.shield_group.add(self.shield)

    def add_wingman(self, offset_x, offset_y):
        wingman = WingMan(offset_x, offset_y, self.spaceship)
        self.wingmen.add(wingman)
        return wingman

    def add_rotating_shield(self):
        sprites = self.rotating_shields.sprites()
        if len(sprites) == 0:
            angle = 0
        elif len(sprites) == 1:
            angle = (sprites[0].angle + 180) % 360
        else:
            angle = 0
        self.rotating_shields.add(RotatingShield(self.spaceship, angle, 100))

    def increase_projectiles(self):
        if self.n_projectiles == 1:  # initial spread
            self.spread = 20
            self.n_projectiles = 2
        else:
            self.n_projectiles += 1
            self.spread *= 1.2
            if self.spread > 90:
                self.spread = 90

    def increase_burst(self):
        self.bursts += 1
        self.fire_cooldown_time *= 0.8 * self.bursts / (self.bursts - 1)


    def wingman_fire(self, x, y):
        self.projectiles.add(Missile(x + 10, y))

    def update(self):
        self.wingmen.update()
        self.rotating_shields.update()

        if self.shield.max_shield > 0:
            self.shield_group.update()

        # Check guns:
        # if keys[pygame.K_SPACE]:
        self.fire()  # automatic fire

        # Guns:
        self.projectiles.update()
        self.fire_cooldown -= 1
        if self.bursts > 0:
            self.burst_cooldown -= 1
        # print(self.burst_cooldown)

    def fire(self):
        if self.fire_cooldown <= 0 or (
                self.current_burst > 0 and self.current_burst < self.bursts and self.burst_cooldown <= 0):
            self.fire_audio.play()
            if self.n_projectiles == 1:
                angles = [0]
            else:
                angles = np.linspace(-self.spread, self.spread, num=self.n_projectiles)
            for angle in angles:
                speed_x = 16 * math.cos(math.radians(angle))
                speed_y = 16 * math.sin(math.radians(angle)) + self.spaceship.speed_y / 4
                # print(angle, math.cos(math.radians(angle)), math.sin(math.radians(angle)))
                rect = self.spaceship.rect
                projectile = Projectile(rect.right - 10, rect.y + rect.height // 2,
                                        speed_x=speed_x, speed_y=speed_y, angle=angle)
                if self.spaceship.speed_x > 0:
                    projectile.speed_x += self.spaceship.speed_x
                projectile.speed_y += self.spaceship.speed_y / 4
                self.projectiles.add(projectile)
            # cool down reset:
            self.fire_cooldown = self.fire_cooldown_time
            if self.bursts > 0:
                if self.current_burst > 1:
                    self.burst_cooldown = self.burst_cooldown_time
                    self.current_burst -= 1
                else:
                    self.current_burst = self.bursts
                    self.burst_cooldown = self.burst_cooldown_time

    def draw(self, draw_window):
        self.wingmen.draw(draw_window)
        self.rotating_shields.draw(draw_window)

        if self.shield.current_shield > 0:
            self.shield_group.draw(draw_window)

        # Projectiles:
        self.projectiles.draw(draw_window)



class Upgrades(Enum):
    PROJECTILE = 1
    WINGMAN = 2


