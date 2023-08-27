import pygame

from constants import EnemySpawnEvent, NEXT_LEVEL_EVENT

LEVEL_TIMER = 20000
BETWEEN_LEVEL_PAUSE = 5000



class LevelController:
    def __init__(self, game):
        self.levels = self.create_levels()
        self.level_pause = False
        self.game = game
        self.current_level = 0
        pygame.time.set_timer(NEXT_LEVEL_EVENT, LEVEL_TIMER)
        self.activate_next_level()

    def deactivate_all_enemy_events(self):
        for event in EnemySpawnEvent:
            self.activate_event(event, 0)

    @staticmethod
    def activate_event(event, spawn_time):
        print(f"Activating: {event} time:{spawn_time}")
        pygame.time.set_timer(event.value, spawn_time)

    def activate_swarmers(self, spawn_time):
        self.activate_event(EnemySpawnEvent.SWARM, spawn_time)

    def activate_asteroids(self, spawn_time):
        self.activate_event(EnemySpawnEvent.ASTEROID, spawn_time)

    def activate_fireballs(self, spawn_time):
        self.activate_event(EnemySpawnEvent.FIREBALL, spawn_time)

    def activate_slashbullets(self, spawn_time):
        self.activate_event(EnemySpawnEvent.SLASHBULLET, spawn_time)

    def activate_next_level(self):
        # Pause between levels:
        if self.level_pause:
            self.deactivate_all_enemy_events()
            pygame.time.set_timer(NEXT_LEVEL_EVENT, BETWEEN_LEVEL_PAUSE)
            self.level_pause = False
            return

        # New level:
        self.level_pause = True
        pygame.time.set_timer(NEXT_LEVEL_EVENT, LEVEL_TIMER)
        self.current_level += 1
        print(f"NEXT LEVEL: {self.current_level}")
        if self.current_level <= len(self.levels):
            for func, parameters in self.levels[self.current_level - 1]:
                func(*parameters)

    def create_levels(self):
        return [
            # LEVEL 1
            [
                (self.activate_asteroids, [2000])
            ],

            # LEVEL 2
            [
                (self.activate_swarmers, [400])
            ],

            # LEVEL 3
            [
                (self.activate_fireballs, [600]),

            ],

        ]
