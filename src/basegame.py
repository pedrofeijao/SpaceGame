import math
import random
import pygame
import constants
from constants import GameState, WIDTH, HEIGHT, STATUS_BAR_HEIGHT, EnemySpawnEvent
from flying_obj import Planet, Explosion
from enemies import Swarmer, Asteroid, SlashBullet, FireBullet
from init import status_font, title_font
from hero import Spaceship
from levels import LevelController
from moves import SpriteMoves
from utils import scale_and_rotate, group_two_pass_collision, sprite_two_pass_collision


class EnemySpawner:
    def __init__(self, game):
        self.game = game

        # Sprite groups
        self.enemy_ships = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.all_enemies = pygame.sprite.Group()

    def add_enemy_ship_sprite(self, ship):
        self.enemy_ships.add(ship)
        self.all_enemies.add(ship)

    def add_enemy_projectile_sprite(self, projectile):
        self.enemy_projectiles.add(projectile)
        self.all_enemies.add(projectile)

    def spawn_asteroid(self):
        for idx in range(10):  # try a few times to get an asteroid without collision with existing ones
            asteroid = Asteroid(WIDTH, random.randint(100, HEIGHT - 100))
            if pygame.sprite.spritecollide(asteroid, self.enemy_ships, False):
                asteroid.kill()
            else:
                self.add_enemy_ship_sprite(asteroid)
                break

    def spawn_smaller_asteroids(self, asteroid):
        direction = 1 if random.random() > 0.5 else -1
        new_size = asteroid.size - 1
        speed_mult = math.sqrt(4.0 - new_size)
        offset = Asteroid.pixel_size * new_size / 3
        ast1 = Asteroid(asteroid.x - direction * offset, asteroid.y - offset, size=asteroid.size - 1,
                        speed_x=-speed_mult * direction * (0.5 + random.random()),
                        speed_y=-speed_mult * (0.5 + random.random()))
        ast2 = Asteroid(asteroid.x + direction * offset, asteroid.y + offset, size=asteroid.size - 1,
                        speed_x=speed_mult * direction * (0.5 + random.random()),
                        speed_y=speed_mult * (0.5 + random.random()))
        self.add_enemy_ship_sprite(ast1)
        self.add_enemy_ship_sprite(ast2)

    def spawn_random_slash_bullet(self):
        bullet = SlashBullet(self.game.spaceship, WIDTH + 10, random.randint(40, HEIGHT - 40))
        self.add_enemy_projectile_sprite(bullet)

    def spawn_random_fire_bullet(self):
        bullet = FireBullet(self.game.spaceship, WIDTH + 10, random.randint(40, HEIGHT - 40))
        self.add_enemy_projectile_sprite(bullet)

    def check_spawn_events(self, event):

        if event == EnemySpawnEvent.ASTEROID.value:
            self.spawn_asteroid()

        if event == EnemySpawnEvent.SWARM.value:
            swarmer = Swarmer(WIDTH + 20, random.randint(0, HEIGHT), self.game.spaceship)
            self.add_enemy_ship_sprite(swarmer)

        if event == EnemySpawnEvent.FIREBALL.value:
            self.spawn_random_fire_bullet()

        if event == EnemySpawnEvent.SLASHBULLET.value:
            self.spawn_random_slash_bullet()


class Game:
    def __init__(self, window):
        self.level_controller = LevelController(self)
        self.background = Background(window)
        self.window = window
        self.clock = pygame.time.Clock()
        self.state_manager = GameStateManager(self, GameState.RUNNING, window)

        self.spaceship = Spaceship(100, 100)

        self.effects = pygame.sprite.Group()
        self.sprite_moves = SpriteMoves()

        # enemy spawn:
        self.enemy_spawner = EnemySpawner(self)

        # # enemy = Enemy(self, WIDTH + 100, HEIGHT // 2)
        # # self.asteroids.add(enemy)
        # self.sprite_moves.add_relative_move(enemy, -550, 0, time=1.5)
        # self.sprite_moves.add_relative_move(enemy, 0, -200, time=2)

        self.status_bg = scale_and_rotate("assets/Sprites/Space-Gui-2/blue/panel-5.png", (500, 150))

        self.score = 0
        self.next_upgrade = 200000

        self.game_time = 0

    def create_explosion(self, x, y, size):
        explosion = Explosion.create(x, y, size)
        self.effects.add(explosion)

    def check_projectile_hits(self, projectiles, kill_projectile=True):
        # Projectile hits:
        hits = group_two_pass_collision(self.enemy_spawner.enemy_ships, projectiles, False, kill_projectile)
        if hits:
            for enemy, projectiles in hits.items():
                damage = 0
                for projectile in projectiles:
                    damage += projectile.damage
                destroyed = enemy.got_hit(damage=damage)
                if destroyed:
                    # Explosion depending on the size:
                    self.create_explosion(enemy.rect.center[0], enemy.rect.center[1], enemy.size)
                    self.score += enemy.score
                    # Special cases:
                    if type(enemy) == Asteroid and enemy.size > 1:  # breaks the asteroid in 2:

                        self.enemy_spawner.spawn_smaller_asteroids(enemy)

    def check_spaceship_collisions(self):
        # Spaceship collisions:
        hits = sprite_two_pass_collision(self.spaceship, self.enemy_spawner.all_enemies, False)
        if hits:
            for enemy in hits:
                destroyed = enemy.ship_collide(self.spaceship)
                self.spaceship.hit_cooldown = self.spaceship.hit_cooldown_time
                if destroyed:
                    self.score += enemy.score
                    self.create_explosion(enemy.rect.center[0], enemy.rect.center[1], enemy.size)

    def check_rotating_shield_hits(self):
        hits = group_two_pass_collision(self.spaceship.rotating_shields, self.enemy_spawner.enemy_ships, False, False)
        if hits:
            for shield, enemies in hits.items():
                for enemy in enemies:
                    if shield.health <= 0:
                        continue
                    damage = min(shield.damage, enemy.health)
                    shield.health -= damage
                    destroyed = enemy.got_hit(damage=damage)
                    if destroyed:
                        self.create_explosion(enemy.rect.center[0], enemy.rect.center[1], enemy.size)
                        self.score += enemy.score
                if shield.health <= 0:
                    shield.kill()

    def check_shield_hits(self):
        shield = self.spaceship.shield
        # Shield collisions:
        hits = sprite_two_pass_collision(shield, self.enemy_spawner.enemy_ships, False)
        if hits:
            for enemy in hits:
                shield.current_shield -= 1
                shield.shield_recharge = shield.shield_recharge_time
                destroyed = enemy.got_hit(damage=shield.collision_damage)
                if destroyed:
                    self.create_explosion(enemy.rect.center[0], enemy.rect.center[1], enemy.size)

    def event_handling(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state_manager.game_state = GameState.QUIT

            # Game running events:
            if self.state_manager.game_state == GameState.RUNNING:

                self.enemy_spawner.check_spawn_events(event)

                if event.type == constants.NEXT_LEVEL_EVENT:
                    self.level_controller.activate_next_level()

                if event.type == 9998:
                    planet = Planet()
                    self.background.planets.add(planet)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    self.state_manager.game_state = GameState.UPGRADE

                if event.key == pygame.K_1 and len(self.spaceship.wingman_pos) > 0:
                    for i in range(1):
                        pos = self.spaceship.wingman_pos.pop()
                        wingman = self.spaceship.add_wingman(*pos)
                        self.sprite_moves.add_anchored_offset(wingman, -pos[0], -pos[1])
                if event.key == pygame.K_2:
                    self.spaceship.add_rotating_shield()

                if event.key == pygame.K_3:
                    self.spaceship.increase_projectiles()

                if event.key == pygame.K_4:
                    self.spaceship.health += 20

                if event.key == pygame.K_5:
                    self.spaceship.shield.increase_level()


    # Screen drawing functions:
    def draw_status(self):
        """
        Draws the status bar at the top
        """
        pygame.draw.rect(self.window, pygame.Color('black'), pygame.rect.Rect(0, 0, WIDTH, STATUS_BAR_HEIGHT))
        pygame.draw.rect(self.window, pygame.Color('cadetblue2'), pygame.rect.Rect(0, STATUS_BAR_HEIGHT, WIDTH, 3))

        score_text = status_font.render(
            f"Score: {self.score} FPS:{self.clock.get_fps():.0f} Time: {self.game_time:.2f}",
            True, pygame.Color('chartreuse3'))
        self.window.blit(score_text, (WIDTH - 410, 10))

        # Spaceship health:
        pygame.draw.rect(self.window, pygame.Color('gray'), pygame.rect.Rect(6, 6, 208, 38), border_radius=5)
        if self.spaceship.health_bar > self.spaceship.health:
            pygame.draw.rect(self.window, pygame.Color('yellow'),
                             pygame.rect.Rect(10, 10, 2 * self.spaceship.health_bar, 30))
        pygame.draw.rect(self.window, pygame.Color('red'), pygame.rect.Rect(10, 10, 2 * self.spaceship.health, 30))
        if self.spaceship.health_bar < self.spaceship.health:
            pygame.draw.rect(self.window, pygame.Color('blue'), pygame.rect.Rect(10 + 2 * self.spaceship.health_bar, 10,
                                                                                 2 * (
                                                                                         self.spaceship.health - self.spaceship.health_bar),
                                                                                 30))

    # Draws an "action" (running state) frame
    def draw_action(self, add_scroll=True):
        self.background.update_and_draw(add_scroll)
        self.enemy_spawner.all_enemies.draw(self.window)
        self.effects.draw(self.window)
        self.spaceship.draw(self.window)
        self.draw_status()

    def state(self):
        return self.state_manager.game_state

    def update_sprites(self):
        self.spaceship.update()
        self.effects.update()
        self.enemy_spawner.all_enemies.update()

        # Custom sprite moves:
        self.sprite_moves.update()

    def manage_game_state(self, dt):
        self.state_manager.manage_game_state(dt)


class GameStateManager:
    def __init__(self, game: Game, game_state: GameState, window):
        self.game = game
        self.game_state = game_state
        self.window = window

    def manage_game_state(self, dt):
        if self.game_state == GameState.UPGRADE:
            self.upgrade_screen_state()

        if self.game_state == GameState.START_SCREEN:
            self.start_screen_state()

        if self.game_state == GameState.RUNNING:
            self.game_running_state()
            self.game.game_time += dt

        # Upgrade by points:
        if self.game.score >= self.game.next_upgrade and self.game_state == GameState.RUNNING:
            self.game_state = GameState.UPGRADE
            # TODO: move this
            self.game.enemy_spawner.asteroid_timer *= 0.8
            pygame.time.set_timer(EnemySpawnEvent.ASTEROID, round(self.game.enemy_spawner.asteroid_timer))
            self.game.next_upgrade *= 1.5

    def upgrade_screen_state(self):
        self.game.draw_action(add_scroll=False)
        txt = title_font.render("Upgrade time!", False, pygame.Color('chartreuse3'))
        rect = txt.get_rect(center=(WIDTH / 2, 150))
        self.game.window.blit(txt, rect)
        txt_x = rect.left + 50
        txt_y = 250
        for text in ["1 - More speed",
                     "2 - Faster shooting",
                     "3 - +1 Projectile",
                     "4 - Less spread"]:
            txt = status_font.render(text, False, pygame.Color('chartreuse3'))
            rect = txt.get_rect(midleft=(txt_x, txt_y))
            txt_y += 50
            self.game.window.blit(txt, rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_state = GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.game_state = GameState.RUNNING
                    self.game.spaceship.acceleration += 0.1
                if event.key == pygame.K_2:
                    self.game_state = GameState.RUNNING
                    self.game.spaceship.fire_cooldown_time *= 0.8
                if event.key == pygame.K_3:
                    self.game_state = GameState.RUNNING
                    self.game.spaceship.increase_projectiles()
                if event.key == pygame.K_4:
                    self.game_state = GameState.RUNNING
                    self.game.spaceship.spread *= 0.8

    def start_screen_state(self):
        self.game.background.update_and_draw()
        txt = title_font.render("Press Space Bar to Start!", False, pygame.Color('chartreuse3'))
        rect = txt.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        self.game.window.blit(txt, rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_state = GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.game_state = GameState.RUNNING

    def game_running_state(self):
        # Event handling
        self.game.event_handling()

        # Sprite group updates:
        self.game.update_sprites()

        # Check collisions:
        self.game.check_projectile_hits(self.game.spaceship.projectiles)
        self.game.check_spaceship_collisions()

        # Check shields:
        self.game.check_rotating_shield_hits()
        if self.game.spaceship.shield.current_shield > 0:
            self.game.check_shield_hits()

        # Draw screen:
        self.game.draw_action()


class Background:
    def __init__(self, window):
        self.planets = pygame.sprite.Group()
        self.bg = [pygame.image.load(f'assets/bg/bkgd_{idx}.png').convert_alpha() for idx in [1, 2, 3, 5, 7]]
        self.bg_width = self.bg[0].get_width()
        self.scroll = [0] * 8
        self.tiles = math.ceil(WIDTH / self.bg_width) + 1
        self.window = window

    def update_and_draw(self, add_scroll=True):
        self.window.fill((10, 10, 20))
        for tile in range(self.tiles):
            for i, img in enumerate(self.bg):
                self.window.blit(img, (tile * self.bg_width - self.scroll[i], 0))
        if add_scroll:
            self.planets.update()
            base_speed = constants.BG_SPEED
            for idx in range(len(self.scroll)):
                self.scroll[idx] += base_speed
                if self.scroll[idx] > self.bg_width:
                    self.scroll[idx] = 0
                base_speed *= 1.3

        self.planets.draw(self.window)
