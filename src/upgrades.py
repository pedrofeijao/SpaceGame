from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import pygame.event

from src.constants import ANCHORED_OFFSET_EVENT
from src.utils import scale_and_rotate

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
    DAMAGE = 'Increase overall damage'
    SPEED = 'Increase spaceship speed and acceleration'
    SPREAD = 'Reduce basic projectile spread'
    BURST = '+1 burst fire'
    GEM_RADIUS = 'Increase gem pickup range'
    # RECHARGE_TIME = 'Faster recharge weapons/shields'
    # REGENERATE = 'Add/improve health regeneration'
    PROJECTILE_SIZE = 'Larger projectile'

class UpgradeController:
    def __init__(self, spaceship: Spaceship):
        self.spaceship = spaceship

        # Current Upgrade level:
        self.upgrade_level = {
            upgrade: 0 for upgrade in UpgradeType
        }
        self.upgrade_level[UpgradeType.PROJECTILE] = 1


    def apply_upgrade(self, upgrade_type):
        self.upgrade_level[upgrade_type] += 1
        match upgrade_type:
            case UpgradeType.SPEED:
                # No difference per level, just 20% increase.
                self.spaceship.max_speed *= 1.2
                self.spaceship.acceleration *= 1.2

            case UpgradeType.WINGMAN:
                # level 1 and 2, add 2 wingmen;
                match self.upgrade_level[upgrade_type]:
                    case 1 | 2:
                        for i in range(2):
                            pos = self.spaceship.weapons.wingman_pos.pop()
                            wingman = self.spaceship.weapons.add_wingman(*pos)
                            pygame.event.post(pygame.event.Event(ANCHORED_OFFSET_EVENT,
                                                                 target_object=wingman, target_x=-pos[0], target_y=-pos[1],
                                                                 time=1.5))
                    case _: # level 3 and above, increase fire-rate + damage
                        for wingman in self.spaceship.weapons.wingmen.sprites():
                            wingman.firing_speed *= 0.8
                        self.spaceship.weapons.rocket_damage *= 1.5

            case UpgradeType.FIRE_RATE:
                # 15% faster, every level
                self.spaceship.weapons.fire_rate.rate *= 0.85

            case UpgradeType.PROJECTILE:
                # add one projectile, every level.
                self.spaceship.weapons.increase_projectiles()

            case UpgradeType.SHIELD:
                # level 1, 2, and 3, increase max level.
                match self.upgrade_level[upgrade_type]:
                    case 1 | 2 | 3:
                        self.spaceship.weapons.shield.increase_level()
                    case _:  # level 4+ , faster recharge
                        self.spaceship.weapons.shield.shield_recharge_time *= 0.8

            case UpgradeType.BURST:
                # +1 burst, any level
                self.spaceship.weapons.increase_burst()

            case UpgradeType.ROTATING_SHIELD:
                # +2 max rotating shields
                self.spaceship.weapons.rotating_shields_max += 2
                self.spaceship.weapons.rotating_shields_create_idx = 0

            case UpgradeType.MAX_HEALTH:
                # 40% more max health and current health.
                self.spaceship.health = round(self.spaceship.health + 0.4 * self.spaceship.max_health)
                self.spaceship.max_health = round(1.4 * self.spaceship.max_health)

            case UpgradeType.DAMAGE:
                # 30% more damage
                self.spaceship.weapons.rocket_damage *= 1.2
                self.spaceship.weapons.projectile_damage *= 1.2

            case UpgradeType.PROJECTILE_SIZE:
                self.spaceship.weapons.projectile_size += 1
                self.spaceship.weapons.projectile_damage *= 1.4
                self.spaceship.weapons.fire_rate.rate *= 1.2
                self.spaceship.weapons.projectile_size = min(5, self.spaceship.weapons.projectile_size)

            case UpgradeType.GEM_RADIUS:
                self.spaceship.gem_auto_pickup_distance += 100

            case UpgradeType.SPREAD:
                self.spaceship.weapons.spread *= 0.6

            case _:
                print(f"Upgrade {upgrade_type} is not implemented yet!!!")
