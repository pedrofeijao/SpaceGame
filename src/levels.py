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
        if spawn_time:
            print(event_enum, kwargs)
        pygame.time.set_timer(pygame.event.Event(event_id, **kwargs), spawn_time)

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
            Level(0, 500, []),

            # LEVEL 1 - Asteroids
            Level(30000, 1000, [
                (EnemySpawnEvent.ASTEROID, [2000], {}),
                (EnemySpawnEvent.SWARM, [200], {}),
                (EnemySpawnEvent.FIREBALL, [1000], {}),
                (EnemySpawnEvent.SINESHIP, [1000], {}),
                (EnemySpawnEvent.SLASHBULLET, [2000], {}),
            ]),

            # Level 2 - Some swarmers?
            Level(3000, 200, [
                (EnemySpawnEvent.SWARM, [200], {})
            ]),

            Level(3000, 300, [
                (EnemySpawnEvent.SINESHIP, [1500], {'group': 1}),
            ]),
            Level(3000, 300, [
                (EnemySpawnEvent.SINESHIP, [2000], {'group': 2}),
            ]),

            # LEVEL 3
            Level(3000, 5000, [
                (EnemySpawnEvent.ASTEROID, [800], {}),
                (EnemySpawnEvent.FIREBALL, [600], {}),

            ]),
            # LEVEL 4
            Level(3000, 5000, [
                (EnemySpawnEvent.SWARM, [250], {}),
                (EnemySpawnEvent.FIREBALL, [500], {}),
            ]),

        ]


@dataclass
class Level:
    duration: int
    end_pause: int
    spawn_functions: list = field(default_factory=list)
