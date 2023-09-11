import pygame
import math
from queue import Queue

import numpy as np

from src.constants import SHIELD_INITIAL_DAMAGE, FPS, SPACESHIP_DESTROYED
from src.upgrades import UpgradeController

from src.utils import scale_and_rotate, SpriteSheet, ConstantFireRate, BurstFireRate
from src.flying_obj import FlyingObject, AnimatedFO


class Spaceship(FlyingObject):
    acceleration: float

    def __init__(self, x, y, sprite_moves):
        image = scale_and_rotate('assets/Sprites/Ships/spaceShips_003.png', .5, 90)

        # pygame.transform.gaussian_blur()
        self.shadow = pygame.transform.gaussian_blur(
            pygame.mask.from_surface(image, threshold=100).to_surface(unsetcolor=None).convert_alpha()
            , 3)
        super().__init__(image, x, y, health=200, collision_damage=2, hit_color=(255, 0, 0, 100))

        self.acceleration = 0.2
        self.max_speed = 8
        self.brakes = 2

        self.hit_cooldown = 0
        self.hit_cooldown_time = 8

        self.max_health = self.health
        self.health_bar = self.health

        self.gem_auto_pickup_distance = 100

        self.pos_history = Queue()
        self.history_len = 6
        for i in range(self.history_len):
            self.pos_history.put((x, y))
        self.last_pos = self.pos_history.get()

        self.thruster_images = {
            pygame.K_s: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png'),
            pygame.K_w: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', rotate=180),
            # pygame.K_d: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', scale_by=2, rotate=90),
            pygame.K_d: scale_and_rotate('assets/Sprites/Effects/fire18.png', scale_by=1, rotate=90),
            pygame.K_a: scale_and_rotate('assets/Sprites/Effects/spaceEffects_002.png', rotate=-90)}

        self.weapons = WeaponsController(self)
        self.upgrades = UpgradeController(self)

    def update(self):
        keys = self.apply_acceleration()
        self.health = 200
        # Health:
        if self.health > self.max_health:
            self.health = self.max_health
        if self.health <= 0:
            self.youre_dead()
            self.health = 0

        if self.health < self.health_bar:
            self.health_bar -= 1
        if self.health > self.health_bar:
            self.health_bar += 1

        # max speed:
        self.check_max_speed()

        # Update the ship's position based on its velocity
        if self.health > 0:
            self.update_positon()

        # Store position, get last:
        self.pos_history.put((self.x, self.y))
        self.last_pos = self.pos_history.get()

        # Wingmen/Shields
        self.weapons.update()

        # Image:
        super().update_hit_image()

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
        keys = pygame.key.get_pressed()

        # Thrusters:
        if self.health > 0:

            if keys[pygame.K_a]:
                draw_window.blit(self.thruster_images[pygame.K_a],
                                 (self.rect.x + self.rect.width - 10, self.rect.y + 4))
                draw_window.blit(self.thruster_images[pygame.K_a],
                                 (self.rect.x + self.rect.width - 10, self.rect.y + 32))
            if keys[pygame.K_d]:
                draw_window.blit(self.thruster_images[pygame.K_d], (self.rect.x - 35, self.rect.y + 18))

            if keys[pygame.K_w]:
                draw_window.blit(self.thruster_images[pygame.K_w], (self.rect.x - 2, self.rect.y + self.rect.height))
            if keys[pygame.K_s]:
                draw_window.blit(self.thruster_images[pygame.K_s], (self.rect.x - 2, self.rect.y - 30))

            # Spaceship:
            alpha = 10
            for idx, pos in enumerate(self.pos_history.queue):  # shadow
                # if idx % 2 == 0:
                self.shadow.set_alpha(alpha)
                draw_window.blit(self.shadow, self.shadow.get_rect(center=pos))
                alpha += 10
            draw_window.blit(self.image, self.rect.topleft)

        # Weapons:
        self.weapons.draw(draw_window)

    def upgrade(self, upgrade_type):
        self.upgrades.apply_upgrade(upgrade_type)

    def youre_dead(self):
        pygame.event.post(pygame.Event(SPACESHIP_DESTROYED))


class Missile(AnimatedFO):
    def __init__(self, missile_img, x, y, speed_x=3.0, speed_y=0.0, accel_x=0.1, damage=3):
        super().__init__(missile_img, 4, x, y, speed_x, speed_y, accel_x=accel_x)
        self.damage = damage


class WingMan(FlyingObject):
    def __init__(self, wingman_img, x_offset, y_offset, spaceship, firing_speed=100):
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
    def __init__(self, rotating_shield_img, spaceship, angle, max_radius, health=10, radius_speed=1, rotation_speed=6):
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


class Projectile(FlyingObject):

    def __init__(self, image, x, y, speed_x=12.0, speed_y=0.0, damage=1):
        super().__init__(image, x, y, speed_x, speed_y)
        self.damage = damage


class Shield(FlyingObject):
    def __init__(self, spaceship):
        self.frames = {
            idx: scale_and_rotate(f"assets/Sprites/Effects/shield{idx}.png", scale_by=0.8, rotate=-90) for idx in
            [1, 2, 3]
        }
        self.frames[0] = pygame.Surface((0, 0)).convert_alpha()
        super().__init__(self.frames[1], 0, 0, collision_damage=SHIELD_INITIAL_DAMAGE)
        self.max_shield = 0
        self.current_shield = 0
        self.shield_recharge_time = 3 * FPS
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

        self.load_images()

        self.projectiles = pygame.sprite.Group()
        self.projectile_size = 1
        self.spaceship = spaceship
        # self.fire_audio = pygame.mixer.Sound('assets/laserfire01.ogg')
        self.fire_audio = pygame.mixer.Sound('assets/Digital_SFX_Set/laser5.mp3')

        # Main weapon:
        self.projectile_damage = 1
        self.fire_rate = BurstFireRate(rate=FPS * 0.5, burst_rate=FPS * 0.1, bursts=1)

        self.spread = 30
        self.n_projectiles = 6
        self.bursts = 1
        self.current_burst = 1
        self.burst_cooldown_time = 3
        self.burst_cooldown = 0

        # Wingman
        self.wingmen = pygame.sprite.Group()
        self.wingman_pos = [(40, -120), (40, +120), (20, -70), (20, 70)]
        self.rocket_damage = 3

        # Rotating shields
        self.rotating_shields_max = 0
        self.rotating_shields = pygame.sprite.Group()
        self.rotating_shields_create_timer = 5 * FPS
        self.rotating_shields_create_idx = self.rotating_shields_create_timer

        # Shield:
        self.shield = Shield(self.spaceship)
        self.shield_group = pygame.sprite.Group()
        self.shield_group.add(self.shield)

    def load_images(self):
        ROTATING_SHIELD_IMG = 'assets/Sprites/Rocket parts/spaceRocketParts_015.png'
        WINGMAN_IMG = 'assets/Sprites/Ships/spaceShips_002.png'

        self.rotating_shield_img = scale_and_rotate(ROTATING_SHIELD_IMG, scale_by=0.9, rotate=90)
        self.wingman_img = scale_and_rotate(WINGMAN_IMG, scale_by=0.3, rotate=90)

        # PROJECTILE_IMGS = {
        #     angle: scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue02.png", (13, 37), angle) for angle in range(361)
        # }
        # projectile_img = [scale_and_rotate(f"assets/Sprites/Laser Sprites/{i:02d}.png", (40, 40)) for i in range(1, 11)]
        # image = Projectile.projectile_img[random.randint(0, len(Projectile.projectile_img) - 1)]
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/01.png", (40, 40), -angle)
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/28.png", (105, 46), -angle)
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue06.png", (7, 19), 90 - angle)
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue02.png", (13, 37), -angle % 360)
        # image = PROJECTILE_IMGS[round((90 - angle) % 360)]
        # image = scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue01.png", (9, 54), 90 - angle)
        self.projectile_imgs = {
            (size, angle): scale_and_rotate(f"assets/Sprites/Laser Sprites/laserBlue06.png", 0.35 * (size + 1), angle)
            for size in [1, 2, 3, 4, 5] for angle in
            range(361)
        }
        ROCKET_SPRITE_SHEET = "assets/Sprites/Missiles/projectile_rocket_16x16.png"

        missile_sprites = SpriteSheet(
            pygame.image.load(ROCKET_SPRITE_SHEET).convert_alpha())
        self.missile_img = [missile_sprites.get_image(idx, 4, 16, 16, 3) for idx in [1, 2, 3]]

    def add_wingman(self, offset_x, offset_y):
        wingman = WingMan(self.wingman_img, offset_x, offset_y, self.spaceship)
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
        self.rotating_shields.add(RotatingShield(self.rotating_shield_img, self.spaceship, angle, 100))

    def kill_rotating_shield(self, shield):
        shield.kill()
        self.rotating_shields_create_idx = self.rotating_shields_create_timer

    def increase_projectiles(self):
        if self.n_projectiles == 1:  # initial spread
            self.spread = 20
            self.n_projectiles = 2
        else:
            self.n_projectiles += 2
            self.spread *= 1.5
            if self.spread > 90:
                self.spread = 90

    def increase_burst(self):
        self.fire_rate.bursts += 2
        self.bursts += 2
        self.fire_rate.rate *= 0.8 * self.bursts / (self.bursts - 2)

    def wingman_fire(self, x, y):
        self.projectiles.add(Missile(self.missile_img, x + 10, y, damage=self.rocket_damage))

    def update(self):
        self.wingmen.update()

        # Rot shields
        self.rotating_shields.update()
        self.rotating_shields_create_idx -= 1
        if self.rotating_shields_create_idx <= 0 and len(self.rotating_shields) < self.rotating_shields_max:
            self.add_rotating_shield()
            self.rotating_shields_create_idx = self.rotating_shields_create_timer

        if self.shield.max_shield > 0:
            self.shield_group.update()

        # Check guns:
        # if keys[pygame.K_SPACE]:
        can_fire = self.spaceship.weapons.fire_rate.update_and_check_fire()
        if self.spaceship.health > 0 and can_fire:
            self.fire()  # automatic fire

        # update projectiles:
        self.projectiles.update()

    def fire(self):

        self.fire_audio.play()
        match self.n_projectiles:
            case 1:
                self.create_projectile(speed=16, angle=0, damage=self.projectile_damage)
            case _:
                self.create_projectile(speed=16, angle=0, damage=self.projectile_damage, y_offset=-15)
                self.create_projectile(speed=16, angle=0, damage=self.projectile_damage, y_offset=+15)
                if self.n_projectiles > 2:
                    angles = np.linspace(-self.spread, self.spread, num=self.n_projectiles - 2)
                    for angle in angles:
                        self.create_projectile(speed=16, angle=angle, damage=self.projectile_damage)

    def draw(self, draw_window):
        self.wingmen.draw(draw_window)
        self.rotating_shields.draw(draw_window)

        if self.shield.current_shield > 0:
            self.shield_group.draw(draw_window)

        # Projectiles:
        self.projectiles.draw(draw_window)

    def create_projectile(self, angle, speed=16, damage=1, y_offset=0):
        speed_x = speed * math.cos(math.radians(angle))
        speed_y = speed * math.sin(math.radians(angle)) + self.spaceship.speed_y / 4
        rect = self.spaceship.rect
        image = self.projectile_imgs[self.spaceship.weapons.projectile_size, round((90 - angle) % 360)]

        projectile = Projectile(image, rect.right - 10, rect.y + rect.height // 2 + y_offset,
                                speed_x=speed_x, speed_y=speed_y, damage=damage)
        if self.spaceship.speed_x > 0:
            projectile.speed_x += self.spaceship.speed_x
        projectile.speed_y += self.spaceship.speed_y / 4
        self.projectiles.add(projectile)
