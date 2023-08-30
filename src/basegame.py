import math
import pygame
from src.constants import GameState, WIDTH, HEIGHT, STATUS_BAR_HEIGHT, NEXT_LEVEL_EVENT, HEALTH_POS_LEFT, \
    HEALTH_POS_TOP, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT, BG_SPEED
from src.flying_obj import Planet, Explosion
from src.enemies import Asteroid
from src.init import status_font, title_font
from src.hero import Spaceship
from src.levels import LevelController
from src.moves import SpriteMoves
from src.enemy_spawner import EnemySpawner
from src.utils import scale_and_rotate, group_two_pass_collision, sprite_two_pass_collision
from src import gradient


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

        self.score = 0
        self.upgrade_level = 1
        self.next_upgrade = self.calc_next_upgrade()

        self.game_time = 0

    def calc_next_upgrade(self):
        return self.upgrade_level * (self.upgrade_level + 1) * 40

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
        hits = group_two_pass_collision(self.spaceship.weapons.rotating_shields, self.enemy_spawner.enemy_ships, False, False)
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
        shield = self.spaceship.weapons.shield
        # Shield collisions:
        hits = sprite_two_pass_collision(shield, self.enemy_spawner.all_enemies, False)
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

                if event.type == NEXT_LEVEL_EVENT:
                    self.level_controller.activate_next_level()

                if event.type == 9998:
                    planet = Planet()
                    self.background.planets.add(planet)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    self.state_manager.game_state = GameState.UPGRADE
                if event.key == pygame.K_1 and len(self.spaceship.weapons.wingman_pos) > 0:
                    for i in range(1):
                        pos = self.spaceship.weapons.wingman_pos.pop()
                        wingman = self.spaceship.weapons.add_wingman(*pos)
                        self.sprite_moves.add_anchored_offset(wingman, -pos[0], -pos[1])
                if event.key == pygame.K_2:
                    self.spaceship.weapons.add_rotating_shield()

                if event.key == pygame.K_3:
                    self.spaceship.weapons.increase_projectiles()

                if event.key == pygame.K_4:
                    self.spaceship.health += 20

                if event.key == pygame.K_5:
                    self.spaceship.weapons.shield.increase_level()

                if event.key == pygame.K_6:
                    self.spaceship.health -= 20

                if event.key == pygame.K_7:
                    self.spaceship.weapons.increase_burst()

    # Screen drawing functions:
    def draw_status(self):
        """
        Draws the status bar at the top
        """

        pygame.draw.rect(self.window, pygame.Color('black'), pygame.rect.Rect(0, 0, WIDTH, STATUS_BAR_HEIGHT))
        pygame.draw.rect(self.window, pygame.Color('cadetblue2'), pygame.rect.Rect(0, STATUS_BAR_HEIGHT, WIDTH, 3))

        score_text = status_font.render(
            f"Score: {self.score}/{self.next_upgrade}  Level: {self.level_controller.current_level}     FPS:{self.clock.get_fps():.0f}      Time: {self.game_time:.0f}",
            True, pygame.Color('chartreuse3'))
        self.window.blit(score_text, (400, 10))

        # Spaceship health:
        # Background



        pygame.draw.rect(self.window, pygame.Color('gray40'), pygame.rect.Rect(HEALTH_POS_LEFT-1, HEALTH_POS_TOP-1, HEALTH_BAR_WIDTH+2, HEALTH_BAR_HEIGHT+2), border_radius=0)
        HEART_IMG = scale_and_rotate("assets/Sprites/PowerUp/heart.png", 0.5)
        self.window.blit(HEART_IMG, (HEALTH_POS_LEFT - 25, HEALTH_POS_TOP - 5))

        # self.window.blit(gradient.vertical((HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT), pygame.Color('red'), pygame.Color('red')),
        #                  (HEALTH_POS_LEFT, HEALTH_POS_TOP))
        pygame.draw.rect(self.window, pygame.Color('red'),
                         pygame.rect.Rect(HEALTH_POS_LEFT, HEALTH_POS_TOP, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT))

        health_size = round(self.spaceship.health/100 * HEALTH_BAR_WIDTH)
        damage_size = round((self.spaceship.health_bar - self.spaceship.health)/100 * HEALTH_BAR_WIDTH)
        health_pos = health_size + HEALTH_POS_LEFT

        health_gain_pos = round(self.spaceship.health_bar/100 * HEALTH_BAR_WIDTH) + HEALTH_POS_LEFT
        health_gain_size = health_pos - health_gain_pos

        # pygame.draw.rect(self.window, pygame.Color('gray'),
        #                  pygame.rect.Rect(health_pos, 10, W - health_size, 15))

        if self.spaceship.health < 100:

            self.window.blit(gradient.horizontal((HEALTH_BAR_WIDTH-health_size, HEALTH_BAR_HEIGHT), pygame.Color('gray60'), pygame.Color('gray30')),
                         (health_pos, HEALTH_POS_TOP))


        if self.spaceship.health_bar > self.spaceship.health:
            # pygame.draw.rect(self.window, pygame.Color('orange1'),
            #                  pygame.rect.Rect(health_pos, TOP, damage_size, H))
            self.window.blit(gradient.horizontal((damage_size, HEALTH_BAR_HEIGHT), pygame.Color('red'), pygame.Color('yellow')),
                         (health_pos, HEALTH_POS_TOP))
        if self.spaceship.health_bar < self.spaceship.health:
            self.window.blit(gradient.horizontal((health_gain_size, HEALTH_BAR_HEIGHT),
                                                 pygame.Color('red'), pygame.Color('blue')),
                         (health_gain_pos, HEALTH_POS_TOP))


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
            self.game.upgrade_level += 1
            self.game.next_upgrade = self.game.calc_next_upgrade()

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
                    self.game.spaceship.weapons.fire_cooldown_time *= 0.8
                if event.key == pygame.K_3:
                    self.game_state = GameState.RUNNING
                    self.game.spaceship.weapons.increase_projectiles()
                if event.key == pygame.K_4:
                    self.game_state = GameState.RUNNING
                    self.game.spaceship.weapons.spread *= 0.8

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
        self.game.check_projectile_hits(self.game.spaceship.weapons.projectiles)
        self.game.check_spaceship_collisions()

        # Check shields:
        self.game.check_rotating_shield_hits()
        if self.game.spaceship.weapons.shield.current_shield > 0:
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
            base_speed = BG_SPEED
            for idx in range(len(self.scroll)):
                self.scroll[idx] += base_speed
                if self.scroll[idx] > self.bg_width:
                    self.scroll[idx] = 0
                base_speed *= 1.3

        self.planets.draw(self.window)
