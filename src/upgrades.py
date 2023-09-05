from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import pygame.event

from src.constants import ANCHORED_OFFSET_EVENT

if TYPE_CHECKING:
    from src.hero import Spaceship


class UpgradeType(Enum):
    MAX_HEALTH = '40% more health'
    PROJECTILE = '+1 Basic Weapon Projectile'
    WINGMAN = 'Add/improve Wingmen'
    ROTATING_SHIELD = '+2 rotating Shields'
    # MINES = '+1 Mines'
    # LASER = 'Add/improve Laser weapon'
    # PULSE_BEAM = 'Add/improve Defensive pulse beam'
    SHIELD = 'Add/improve Power shield'
    FIRE_RATE = 'Increase fire rate'
    # DAMAGE = 'Increase damage'
    SPEED = 'Increase spaceship speed and acceleration'
    SPREAD = 'Reduce basic projectile spread'
    BURST = '+1 burst fire'
    # RECHARGE_TIME = 'Faster recharge weapons/shields'
    # REGENERATE = 'Add/improve health regeneration'


class UpgradeController:
    def __init__(self, spaceship: Spaceship):
        self.spaceship = spaceship

        # Weapons:
        self.projectile_level = 1
        self.wingman_level = 0
        self.rotating_shield_level = 0
        self.mines_level = 0
        self.laser_level = 0
        self.pulse_beam_level = 0
        self.burst_level = 0

        # Upgrades:
        self.shield_level = 0
        self.fire_rate_level = 0
        self.damage_level = 0
        self.projectile_size_level = 0
        self.speed_level = 0

    def apply_upgrade(self, upgrade_type):
        match upgrade_type:
            case UpgradeType.SPEED:
                self.speed_level += 1
                self.spaceship.max_speed *= 1.2
                self.spaceship.acceleration *= 1.2

            case UpgradeType.WINGMAN:
                if len(self.spaceship.weapons.wingman_pos) > 0:
                    for i in range(2):
                        pos = self.spaceship.weapons.wingman_pos.pop()
                        wingman = self.spaceship.weapons.add_wingman(*pos)
                        pygame.event.post(pygame.event.Event(ANCHORED_OFFSET_EVENT,
                                                             target_object=wingman, target_x=-pos[0], target_y=-pos[1],
                                                             time=1.5))

            case UpgradeType.FIRE_RATE:
                self.fire_rate_level += 1
                self.spaceship.weapons.fire_cooldown_time *= 0.85

            case UpgradeType.PROJECTILE:
                self.projectile_level += 1
                self.spaceship.weapons.increase_projectiles()

            case UpgradeType.SHIELD:
                self.spaceship.weapons.shield.increase_level()

            case UpgradeType.BURST:
                self.burst_level += 1
                self.spaceship.weapons.increase_burst()

            case UpgradeType.ROTATING_SHIELD:
                self.spaceship.weapons.rotating_shields_max += 2
                self.spaceship.weapons.rotating_shields_create_idx = 0

            case UpgradeType.MAX_HEALTH:
                self.spaceship.health = round(self.spaceship.health + 0.4 * self.spaceship.max_health)
                self.spaceship.max_health = round(1.4 * self.spaceship.max_health)

            case _:
                print(f"Upgrade {upgrade_type} is not implemented yet!!!")
