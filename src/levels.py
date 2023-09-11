from dataclasses import dataclass, field
from queue import Queue, PriorityQueue
from typing import Any

import pygame

from src.constants import EnemySpawnEvent, NEXT_LEVEL_EVENT

LEVEL_TIMER = 20000
BETWEEN_LEVEL_PAUSE = 5000


class LevelController:
    def __init__(self, game):
        self.next_level_time = 0
        self.levels = LevelController.create_levels()
        self.level_pause = True
        self.game = game
        self.current_level = 1
        self.enemy_queue = PriorityQueue()

    def activate_next_level(self):

        level = self.levels.get()
        print(f"ACTIVATE {level}")
        # Check new level, or just wave:
        if level.increase_level:
            self.current_level += 1
        # Check timer to trigger next level. If 0, means some enemy (usually boss) will trigger the next level when dead
        if level.duration > 0:
            print(f"Next in {level.duration} ms.")
            self.next_level_time += level.duration

        # Activate all enemies:
        for level_enemy in level.level_enemies:
            print(f"Activate: {level_enemy.event}")
            level_enemy.activate(self.game.game_time, self.enemy_queue)

    def update(self):
        # check next level:
        if self.game.game_time > self.next_level_time:
            self.activate_next_level()

        # Check enemy events by time and post them:
        while self.enemy_queue.qsize() > 0:
            event = self.enemy_queue.get()
            if event[0] <= self.game.game_time:
                pygame.event.post(event[1].item)
            else:
                self.enemy_queue.put(event)
                break



    @staticmethod
    def create_levels():
        levels = Queue()
        for level in [
            # Level 1
            Level(30, [
                LevelEnemy(EnemySpawnEvent.ASTEROID, 2, loops=15),
            ]),

            Level(30, [
                LevelEnemy(EnemySpawnEvent.ASTEROID, spawn_time=2, loops=15),
                LevelEnemy(EnemySpawnEvent.SWARM, spawn_time=0.5, loops=60)
            ]),

            Level(4000, [
                LevelEnemy(EnemySpawnEvent.SWARM, spawn_time=100, loops=20),
            ]),

            Level(4000, [
                LevelEnemy(EnemySpawnEvent.SWARM, 100, loops=20),
            ], increase_level=True),

            Level(4000, [
                LevelEnemy(EnemySpawnEvent.SWARM, 100, loops=20),
            ]),

            Level(10000, [
                LevelEnemy(EnemySpawnEvent.ASTEROID, 3000),
                LevelEnemy(EnemySpawnEvent.SWARM, 2000)
            ]),
            Level(10000, [
                LevelEnemy(EnemySpawnEvent.ASTEROID, 3000),
                LevelEnemy(EnemySpawnEvent.SWARM, 1000)
            ]),
            Level(10000, [
                LevelEnemy(EnemySpawnEvent.ASTEROID, 1500),
                LevelEnemy(EnemySpawnEvent.SWARM, 300)
            ]),

            Level(10000, [
                LevelEnemy(EnemySpawnEvent.SWARM, 500),
                LevelEnemy(EnemySpawnEvent.SINESHIP, 2000, event_kwargs={'shoot_time': 3, 'level': 1}),
            ]),

            Level(10000, [
                LevelEnemy(EnemySpawnEvent.SWARM, 500),
                LevelEnemy(EnemySpawnEvent.SINESHIP, 2000, event_kwargs={'shoot_time': 3, 'group': 2, 'level': 1}),
            ]),

            Level(0, [
                LevelEnemy(EnemySpawnEvent.SPREADBOSS, 1),
            ]),
        ]:
            levels.put(level)
        return levels



@dataclass
class LevelEnemy:
    event: EnemySpawnEvent
    spawn_time: float  # in secs
    loops: int = 0
    event_kwargs: dict = field(default_factory=dict)

    def activate(self, current_time, queue: PriorityQueue):
        event = pygame.event.Event(self.event.value, **self.event_kwargs)
        print(self.event, self.spawn_time)
        dt = 0
        for idx in range(self.loops):
            priority = current_time + dt
            event = PrioritizedEvent(priority=priority, item=pygame.event.Event(self.event.value, **self.event_kwargs))
            queue.put((priority, event))
            dt += self.spawn_time
        # pygame.time.set_timer(event, self.spawn_time, loops=self.loops)


@dataclass
class Level:
    duration: int
    level_enemies: list[LevelEnemy] = field(default_factory=list)
    increase_level: bool = False


@dataclass(order=True)
class PrioritizedEvent:
    priority: int
    item: Any=field(compare=False)