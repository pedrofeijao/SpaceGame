from dataclasses import dataclass, field

import pygame

from src.constants import EnemySpawnEvent, NEXT_LEVEL_EVENT

LEVEL_TIMER = 20000
BETWEEN_LEVEL_PAUSE = 5000


class LevelController:
    def __init__(self, game):
        self.levels = LevelController.create_levels()
        self.level_pause = True
        self.game = game
        self.current_level = 0
        self.activate_next_level()

    def deactivate_all_enemy_events(self):
        for event_enum in EnemySpawnEvent:
            self.activate_event(event_enum, 0)

    @staticmethod
    def activate_event(event_enum, spawn_time, **kwargs):
        event_id = event_enum.value
        event = pygame.event.Event(event_id, **kwargs)
        if spawn_time > 0:
            print(event_id, spawn_time)
        if spawn_time == 1: # spawn time of 1 means a single event, instead of timer
            pygame.event.post(event)
        else:
            pygame.time.set_timer(event, spawn_time)

    def activate_next_level(self):
        # Pause between levels:
        if self.level_pause:
            self.deactivate_all_enemy_events()
            pygame.time.set_timer(NEXT_LEVEL_EVENT, self.levels[self.current_level].end_pause)
            self.level_pause = False
            return

        # New level:
        self.level_pause = True
        self.current_level += 1

        pygame.time.set_timer(NEXT_LEVEL_EVENT, self.levels[self.current_level].duration)
        if self.current_level < len(self.levels):
            for event_enum, spawn_time, kwargs in self.levels[self.current_level].spawn_functions:
                self.activate_event(event_enum, *spawn_time, **kwargs)

    @staticmethod
    def create_levels():
        return [
            # Level 0
            Level(10, 200, []),

            Level(20000, 2000, [
                (EnemySpawnEvent.SINESHIP, [1000], {'shoot_time': 2, 'level': 2}),
            ]),

            Level(20000, 2000, [
                (EnemySpawnEvent.SPREADBOSS, [1], {}),
            ]),

            #
            # Level(20000, 2000, [
            #     (EnemySpawnEvent.CHASERSHIP, [1], {}),
            # ]),

            Level(30000, 2000, [
                (EnemySpawnEvent.ASTEROID, [2000], {}),
                (EnemySpawnEvent.SWARM, [500], {})
            ]),

            # LEVEL 1 - Asteroids
            Level(30000, 2000, [
                (EnemySpawnEvent.ASTEROID, [1200], {})
            ]),

            Level(30000, 2000, [
                (EnemySpawnEvent.ASTEROID, [2000], {}),
                (EnemySpawnEvent.SWARM, [500], {})
            ]),

            Level(30000, 5000, [
                (EnemySpawnEvent.ASTEROID, [2000], {}),
                (EnemySpawnEvent.SWARM, [250], {})
            ]),

            Level(30000, 2000, [
                (EnemySpawnEvent.SINESHIP, [1500], {})
            ]),

            Level(30000, 300, [
                (EnemySpawnEvent.SINESHIP, [1500], {'group': 2}),
            ]),

            Level(30000, 300, [
                (EnemySpawnEvent.SINESHIP, [2000], {'group': 3}),
            ]),

            Level(30000, 3000, [
                (EnemySpawnEvent.SWARM, [500], {}),
                (EnemySpawnEvent.SINESHIP, [2000], {'group': 2}),
            ]),

            Level(30000, 300, [
                (EnemySpawnEvent.FIREBALL, [1000], {}),
            ]),
            Level(30000, 300, [
                (EnemySpawnEvent.SWARM, [500], {}),
                (EnemySpawnEvent.FIREBALL, [1000], {}),
            ]),
            Level(30000, 300, [
                (EnemySpawnEvent.SWARM, [500], {}),
                (EnemySpawnEvent.FIREBALL, [1000], {}),
                (EnemySpawnEvent.SINESHIP, [2000], {'group': 2}),
            ]),

            Level(30000, 300, [
                (EnemySpawnEvent.SLASHBULLET, [2000], {}),
            ]),
            Level(30000, 300, [
                (EnemySpawnEvent.SWARM, [500], {}),
                (EnemySpawnEvent.SLASHBULLET, [2000], {}),
            ]),
            Level(30000, 300, [
                (EnemySpawnEvent.SWARM, [500], {}),
                (EnemySpawnEvent.SLASHBULLET, [1500], {}),
                (EnemySpawnEvent.SINESHIP, [2000], {'group': 2}),
            ]),

            Level(60000, 1000, [
                (EnemySpawnEvent.ASTEROID, [2000], {}),
                (EnemySpawnEvent.SWARM, [600], {}),
                (EnemySpawnEvent.FIREBALL, [3000], {}),
                (EnemySpawnEvent.SINESHIP, [2000], {'group': 3}),
                (EnemySpawnEvent.SLASHBULLET, [3000], {}),
            ]),

            Level(600000, 1000, [
                (EnemySpawnEvent.ASTEROID, [1500], {}),
                (EnemySpawnEvent.SWARM, [400], {}),
                (EnemySpawnEvent.FIREBALL, [2000], {}),
                (EnemySpawnEvent.SINESHIP, [1000], {'group': 3}),
                (EnemySpawnEvent.SLASHBULLET, [2000], {}),
            ]),

        ]


@dataclass
class Level:
    duration: int
    end_pause: int
    spawn_functions: list = field(default_factory=list)
