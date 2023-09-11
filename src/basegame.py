import math
import random

from src import gradient
from src.constants import *
from src.enemies import Asteroid, Swarmer, SineShip, HealthBarEnemy, SpreadBulletBoss
from src.enemy_spawner import EnemySpawner
from src.flying_obj import Planet, Explosion, Damage, FlyingObject, UpgradePoint
from src.gui import SelectBox
from src.hero import Spaceship
from src.levels import LevelController
from src.moves import SpriteMoves
from src.upgrades import UpgradeType
from src.utils import scale_and_rotate, group_two_pass_collision, sprite_two_pass_collision


class Game:
    def __init__(self):
        # init pygame:
        # Set the dimensions of the window
        # pygame.display.set_caption("Spaceship Simulation")
        pygame.init()
        self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # self.window = pygame.display.set_mode((1200,800))

        self.width = self.window.get_width()
        self.height = self.window.get_height()
        # window = Window(size=window_size)
        # renderer = Renderer(window)
        # renderer.draw_color = (0, 0, 0, 255)

        # graphics: move?
        self.status_font = pygame.font.Font('assets/fonts/Grand9K Pixel.ttf', 24)
        self.title_font = pygame.font.Font('assets/fonts/Grand9K Pixel.ttf', 64)
        self.background = Background(self.window)

        # Upgrade icons:
        self.upgrade_icon = {
            UpgradeType.BURST: scale_and_rotate('assets/icons/icons8-double-up-100_2.png', size=(60, 60)),
            UpgradeType.SPEED: scale_and_rotate('assets/icons/icons8-rocket-78.png', size=(60, 60)),
            UpgradeType.PROJECTILE: scale_and_rotate('assets/icons/icons8-parallel-symbol-100.png', size=(60, 60)),
            UpgradeType.FIRE_RATE: scale_and_rotate('assets/icons/icons8-rocket-64.png', size=(60, 60)),
            UpgradeType.ROTATING_SHIELD: scale_and_rotate('assets/icons/icons8-filled-circle-100.png', size=(60, 60)),
            UpgradeType.DAMAGE: scale_and_rotate('assets/icons/icons8-damage-64.png', size=(60, 60)),
            UpgradeType.WINGMAN: scale_and_rotate('assets/icons/icons8-spaceship-90.png', size=(60, 60)),
            UpgradeType.SHIELD: scale_and_rotate('assets/icons/icons8-shield-100.png', size=(60, 60)),
            UpgradeType.MAX_HEALTH: scale_and_rotate('assets/icons/icons8-health-100.png', size=(60, 60)),
            UpgradeType.SPREAD: scale_and_rotate('assets/icons/icons8-waves-100.png', size=(60, 60)),
            UpgradeType.PROJECTILE_SIZE: scale_and_rotate('assets/icons/icons8-up-squared-100.png', size=(60, 60)),
            UpgradeType.GEM_RADIUS: scale_and_rotate('assets/icons/icons8-laser-100.png', size=(60, 60)),

        }
        self.small_upgrade_icon = {upgrade: pygame.transform.scale_by(image, 0.5) for upgrade, image in
                                   self.upgrade_icon.items()}
        self.clock = pygame.time.Clock()
        self.start_up()

        # audio: move to better place?
        self.gem_audio = pygame.mixer.Sound('assets/Digital_SFX_Set/powerUp2.mp3')

    def start_up(self):
        self.state_manager = GameStateManager(self, GameState.START_SCREEN, self.window)

        self.effects = pygame.sprite.Group()
        self.sprite_moves = SpriteMoves()

        self.spaceship = Spaceship(100, self.height // 2, self.sprite_moves)
        self.level_controller = LevelController(self)

        # enemy spawn:
        self.enemy_spawner = EnemySpawner(self)


        self.score = 0
        self.upgrade_score = 0
        self.upgrade_level = 1
        self.next_upgrade = self.calc_next_upgrade()

        self.game_time = 0

    def calc_next_upgrade(self):
        return 100 * (self.upgrade_level + 1)

    def create_explosion(self, x, y, size):
        explosion = Explosion.create(x, y, size)
        self.effects.add(explosion)

    def create_damage_marker(self, x, y, damage):
        sprite = Damage(x, y, round(10 * damage), self.status_font)
        self.effects.add(sprite)

    def create_upgrade_points_marker(self, x, y, points):
        sprite = UpgradePoint(x, y, points, self.status_font)
        self.effects.add(sprite)

    def check_projectile_hits(self, projectiles, kill_projectile=False):
        # Projectile hits:
        hits = group_two_pass_collision(self.enemy_spawner.enemy_ships, projectiles, False, kill_projectile)
        if hits:
            for enemy, projectiles in hits.items():
                damage = 0
                for projectile in projectiles:
                    damage += projectile.damage
                    self.create_damage_marker(projectile.x, projectile.y, projectile.damage)
                    projectile.health -= 1
                    if projectile.health == 0:
                        projectile.kill()
                destroyed = enemy.got_hit(damage=damage)
                if destroyed:
                    self.enemy_destroyed(enemy)

    def check_spaceship_collisions(self):
        # Spaceship collisions:
        hits = sprite_two_pass_collision(self.spaceship, self.enemy_spawner.all_enemies, False)
        if hits:
            for enemy in hits:
                destroyed = enemy.ship_collide(self.spaceship)
                self.spaceship.hit_cooldown = self.spaceship.hit_cooldown_time
                if destroyed:
                    self.enemy_destroyed(enemy)

        # GEMS:
        hits = sprite_two_pass_collision(self.spaceship, self.enemy_spawner.gems, False)
        if hits:
            for gem in hits:
                gem.kill()
                self.create_upgrade_points_marker(gem.x, gem.y, gem.upgrade_score)
                self.gem_audio.play()
                self.upgrade_score += gem.upgrade_score

    def check_rotating_shield_hits(self):
        hits = group_two_pass_collision(self.spaceship.weapons.rotating_shields, self.enemy_spawner.enemy_ships, False,
                                        False)
        if hits:
            for shield, enemies in hits.items():
                for enemy in enemies:
                    if shield.health <= 0:
                        continue
                    damage = min(shield.damage, enemy.health)
                    self.create_damage_marker(shield.x, shield.y, shield.damage)
                    shield.health -= damage
                    destroyed = enemy.got_hit(damage=damage)
                    if destroyed:
                        self.enemy_destroyed(enemy)
                if shield.health <= 0:
                    self.spaceship.weapons.kill_rotating_shield(shield)

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
                    self.enemy_destroyed(enemy)

    def enemy_destroyed(self, enemy):
        # Explosion depending on the size:
        self.create_explosion(enemy.rect.center[0], enemy.rect.center[1], enemy.size)
        self.score += enemy.score
        # Special cases:
        if isinstance(enemy, Asteroid) and enemy.size > 1:  # breaks the asteroid in 2:
            self.enemy_spawner.spawn_smaller_asteroids(enemy)
        # Gem: each enemy might spawn a different type at some point. For now all the same
        if isinstance(enemy, Swarmer):
            self.enemy_spawner.spawn_gem(enemy.x, enemy.y, n_gems=1, level=1)
        if isinstance(enemy, Asteroid) and enemy.size == 1:
            self.enemy_spawner.spawn_gem(enemy.x, enemy.y, n_gems=2)
        if isinstance(enemy, SineShip):
            self.enemy_spawner.spawn_gem(enemy.x, enemy.y, n_gems=2, level=2)
        if isinstance(enemy, SpreadBulletBoss):
            self.enemy_spawner.spawn_gem(enemy.x, enemy.y, n_gems=6, level=2)

    def process_event(self, event):
        if event.type == pygame.QUIT:
            self.state_manager.game_state = GameState.QUIT

        if event.type == NEXT_LEVEL_EVENT:
            self.level_controller.activate_next_level()

        self.enemy_spawner.check_spawn_events(event)

        if event.type == PLANET_EVENT:
            self.background.spawn_planet()
        if event.type == ANCHORED_OFFSET_EVENT:
            self.sprite_moves.add_anchored_offset(**event.dict)
        if event.type == ABSOLUTE_MOVE_EVENT:
            self.sprite_moves.add_absolute_move(**event.dict)
        if event.type == SPACESHIP_DESTROYED:
            self.spaceship_destroyed_sequence()
            self.state_manager.game_state = GameState.GAME_OVER
        if event.type == SIMPLE_BULLET_EVENT:
            self.enemy_spawner.spawn_simple_bullet(**event.dict)
        if event.type == TARGETED_ROUND_BULLET_EVENT:
            self.enemy_spawner.spawn_targeted_round_bullet(**event.dict)
        if event.type == ANGLED_ROUND_BULLET_EVENT:
            self.enemy_spawner.spawn_angled_round_bullet(**event.dict)

        # Keys and specific game events:
        if self.state_manager.game_state == GameState.GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.start_up()
                    self.state_manager.game_state = GameState.RUNNING


            # if event.key == pygame.K_7:
            #     self.spaceship.weapons.increase_burst()
            # if event.key == pygame.K_g:
            #     self.enemy_spawner.spawn_gem(600, 400)

    # Screen drawing functions:
    def draw_status(self):
        """
        Draws the status bar(s)
        """

        self.draw_top_status_bar()
        self.draw_spaceship_health()
        self.draw_upgrade_status()

    def draw_spaceship_health(self):
        health_bar_width = self.spaceship.max_health
        health_pos_top = self.height - HEALTH_BAR_HEIGHT - 5
        health_pos_left = (self.width - health_bar_width) // 2
        pygame.draw.rect(self.window, pygame.Color('gray40'),
                         pygame.rect.Rect(health_pos_left - 1, health_pos_top - 1, health_bar_width + 2,
                                          HEALTH_BAR_HEIGHT + 2), border_radius=0)
        pygame.draw.rect(self.window, pygame.Color('red'),
                         pygame.rect.Rect(health_pos_left, health_pos_top, health_bar_width, HEALTH_BAR_HEIGHT))
        health_size = round(self.spaceship.health)  # /  * HEALTH_BAR_WIDTH)
        damage_size = round((self.spaceship.health_bar - self.spaceship.health) / 100 * health_bar_width)
        health_pos = health_size + health_pos_left
        health_gain_pos = round(self.spaceship.health_bar / 100 * health_bar_width) + health_pos_left
        if self.spaceship.health < self.spaceship.max_health:
            self.window.blit(
                gradient.horizontal((health_bar_width - health_size, HEALTH_BAR_HEIGHT), pygame.Color('gray60'),
                                    pygame.Color('gray30')),
                (health_pos, health_pos_top))
        if self.spaceship.health_bar > self.spaceship.health:
            # pygame.draw.rect(self.window, pygame.Color('orange1'),
            #                  pygame.rect.Rect(health_pos, TOP, damage_size, H))
            self.window.blit(
                gradient.horizontal((damage_size, HEALTH_BAR_HEIGHT), pygame.Color('red'), pygame.Color('yellow')),
                (health_pos, health_pos_top))

    def draw_top_status_bar(self):
        pygame.draw.rect(self.window, pygame.Color('black'),
                         pygame.rect.Rect(0, 0, self.window.get_width(), STATUS_BAR_HEIGHT))
        pygame.draw.rect(self.window, pygame.Color('cadetblue2'),
                         pygame.rect.Rect(0, STATUS_BAR_HEIGHT, self.window.get_width(), 3))
        score_text = self.status_font.render(
            f"Score: {self.upgrade_score}/{self.next_upgrade}  Time: {self.game_time:.1f}", True, pygame.Color('chartreuse3'))
        self.window.blit(score_text, (10, 10))
        score_text = self.status_font.render(
            f"Level: {self.level_controller.current_level}", True, pygame.Color('chartreuse3'))
        self.window.blit(score_text, (self.width // 2 - 50, 10))
        #
        score_text = self.status_font.render(f"FPS:{self.clock.get_fps():.0f}", True, pygame.Color('chartreuse3'))
        self.window.blit(score_text, (self.width - 100, 10))

    # Draws an "action" (running state) frame
    def draw_action(self, add_scroll=True, spaceship=True):
        self.background.update_and_draw(add_scroll)
        self.enemy_spawner.all_enemies.draw(self.window)

        # health bar:
        for enemy in self.enemy_spawner.all_enemies.sprites():
            if isinstance(enemy, HealthBarEnemy):
                self.draw_health_bar(enemy)

        self.enemy_spawner.gems.draw(self.window)
        self.effects.draw(self.window)
        if spaceship:
            self.spaceship.draw(self.window)
        self.draw_status()

    def state(self):
        return self.state_manager.game_state

    def update_sprites(self):
        self.spaceship.update()
        self.effects.update()
        self.enemy_spawner.all_enemies.update()
        self.enemy_spawner.gems.update()

        # Custom sprite moves:
        self.sprite_moves.update()

    def manage_game_state(self, dt):
        self.state_manager.manage_game_state(dt)

    def check_spaceship_border_hit(self):
        # return
        # Wrap the ship's position if it goes off the screen
        rect = self.spaceship.rect
        if rect.right > self.width:
            self.spaceship.x = self.width - rect.width / 2
            self.spaceship.speed_x *= -0.25
        if rect.left < 0:
            self.spaceship.x = rect.width / 2
            self.spaceship.speed_x *= -0.25
        if rect.bottom > self.height:
            self.spaceship.y = self.height - rect.height / 2
            self.spaceship.speed_y *= -0.25
        if rect.top < STATUS_BAR_HEIGHT:
            self.spaceship.y = STATUS_BAR_HEIGHT + rect.height / 2
            self.spaceship.speed_y *= -0.25
        rect.center = round(self.spaceship.x), round(self.spaceship.y)

    def kill_offbound_sprites(self, sprites):
        for sprite in sprites:
            if sprite.x > self.width + sprite.kill_offset or sprite.x < 0 - sprite.kill_offset:
                sprite.kill()
            if sprite.y > self.height + sprite.kill_offset or sprite.y < 0 - sprite.kill_offset:
                sprite.kill()

    def kill_all_offbound_sprites(self):
        self.kill_offbound_sprites(self.spaceship.weapons.projectiles.sprites())
        self.kill_offbound_sprites(self.enemy_spawner.all_enemies.sprites())

    def spaceship_destroyed_sequence(self):
        self.create_explosion(self.spaceship.x, self.spaceship.y, size=3)
        self.spaceship.weapons.shield.current_shield = self.spaceship.weapons.shield.max_shield = 0
        for wingman in self.spaceship.weapons.wingmen.sprites():
            self.create_explosion(wingman.rect.x, wingman.rect.y, size=1)
            wingman.kill()
        for rot_shield in self.spaceship.weapons.rotating_shields.sprites():
            self.create_explosion(rot_shield.rect.x, rot_shield.rect.y, size=1)
            rot_shield.kill()
        self.spaceship.weapons.rotating_shields_max = 0
        self.spaceship.gem_auto_pickup_distance = -1

    def draw_upgrade_status(self):

        pygame.draw.rect(self.window, pygame.Color('gray40'),
                         pygame.rect.Rect(PROGRESS_BAR_LEFT, PROGRESS_BAR_TOP, self.width,
                                          PROGRESS_BAR_HEIGHT), border_radius=0)
        pygame.draw.rect(self.window, pygame.Color('blue'),
                         pygame.rect.Rect(PROGRESS_BAR_LEFT, PROGRESS_BAR_TOP, self.upgrade_score / self.next_upgrade * self.width,
                                          PROGRESS_BAR_HEIGHT), border_radius=0)

        left_pos = UPGRADE_BAR_LEFT
        for upgrade, level in self.spaceship.upgrades.upgrade_level.items():
            if level == 0:
                continue

            pygame.draw.rect(self.window, pygame.Color('gray50'),
                             pygame.rect.Rect(left_pos, UPGRADE_BAR_TOP, UPGRADE_ICON_SIZE, UPGRADE_ICON_SIZE),
                             border_radius=5)

            icon = self.small_upgrade_icon[upgrade]
            self.window.blit(icon, (left_pos + 5, UPGRADE_BAR_TOP + (UPGRADE_ICON_SIZE - icon.get_height()) // 2))

            txt = self.status_font.render(str(level), False, pygame.Color('white'))
            rect = txt.get_rect(topleft=(left_pos + UPGRADE_ICON_SIZE + 5, UPGRADE_BAR_TOP))
            self.window.blit(txt, rect)

            left_pos += UPGRADE_BAR_SPACING

    def parse_debug_code(self, debug_text: str):
        comm = debug_text.split(" ")
        try:
            match comm[0]:
                case 'sp':
                    self.level_controller.activate_event(EnemySpawnEvent[comm[1].upper()], int(comm[2]))
        except:
            # did not recognize
            pass

    def draw_health_bar(self, enemy: FlyingObject):
        pygame.draw.rect(self.window, pygame.Color('red'),
                         pygame.rect.Rect(enemy.rect.left + 20, enemy.rect.top - 10, enemy.health, 4))


class GameStateManager:
    def __init__(self, game: Game, game_state: GameState, window):
        self.select_box = None
        self.upgrade_choices = None
        self.game = game
        self.game_state = game_state
        self.window = window
        self.debug_text = ""

    def manage_game_state(self, dt):
        if self.game_state == GameState.GAME_OVER:
            self.game_over_state()

        if self.game_state == GameState.UPGRADE:
            self.upgrade_screen_state()

        if self.game_state == GameState.PAUSE:
            self.pause_state()

        if self.game_state == GameState.DEBUG:
            self.debug_state()

        if self.game_state == GameState.START_SCREEN:
            self.start_screen_state()

        if self.game_state == GameState.RUNNING:
            self.game_running_state()
            self.game.game_time += dt


        # Upgrade by points:
        if self.game.upgrade_score >= self.game.next_upgrade and self.game_state == GameState.RUNNING:
            self.game.upgrade_score -= self.game.next_upgrade
            self.game_state = GameState.UPGRADE
            self.game.upgrade_level += 1
            self.game.next_upgrade = self.game.calc_next_upgrade()

    def upgrade_screen_state(self):
        self.game.draw_action(add_scroll=False)

        # Choose upgrades:
        if self.upgrade_choices is None:
            N_CHOICES = 4
            self.upgrade_choices = random.sample(list(UpgradeType), N_CHOICES)
            # icons
            icons = [self.game.upgrade_icon[upgrade] for upgrade in self.upgrade_choices]
            upgrade_text = [upgrade.value for upgrade in self.upgrade_choices]
            height = self.game.height - 200
            option_size = height / (N_CHOICES + 3)
            width = min(900, self.game.width - 200)
            self.select_box = SelectBox(upgrade_text, icons=icons, left=(self.game.width - width) / 2, width=width,
                                        top=100,
                                        height=height, option_size=option_size, top_margin=option_size,
                                        option_spacing=option_size // 2)
        # Box:
        self.select_box.draw(self.window, self.game.status_font)

        # Events:
        for event in pygame.event.get():
            self.game.process_event(event)
            # Specific keys to upgrade:
            if event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_w | pygame.K_UP:
                        self.select_box.select_previous()
                    case pygame.K_s | pygame.K_DOWN:
                        self.select_box.select_next()
                    case pygame.K_RETURN:
                        selected = self.upgrade_choices[self.select_box.selected]
                        self.game.spaceship.upgrade(selected)
                        self.game_state = GameState.RUNNING
                        self.upgrade_choices = None

    def start_screen_state(self):
        self.game.background.update_and_draw()
        txt = self.game.title_font.render("Press Space Bar to Start!", False, pygame.Color('chartreuse3'))
        rect = txt.get_rect(center=(self.game.width / 2, self.game.height / 2))
        self.game.window.blit(txt, rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_state = GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.game.level_controller.activate_next_level()
                    self.game_state = GameState.RUNNING

    def game_running_state(self):

        # Sprite group updates:
        self.game.update_sprites()

        # Check collisions:
        self.game.check_projectile_hits(self.game.spaceship.weapons.projectiles)
        if self.game.spaceship.health > 0:
            self.game.check_spaceship_collisions()

        self.game.check_spaceship_border_hit()

        # Check shields:
        self.game.check_rotating_shield_hits()
        if self.game.spaceship.weapons.shield.current_shield > 0:
            self.game.check_shield_hits()

        # Kill sprites outside of screen:
        self.game.kill_all_offbound_sprites()

        # Check next level trigger / level enemy spawn:
        self.game.level_controller.update()

        # Events:
        for event in pygame.event.get():
            self.game.process_event(event)
            # Specific keys to running:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    self.game_state = GameState.UPGRADE
                if event.key == pygame.K_p:
                    self.game_state = GameState.PAUSE
                if event.key == pygame.K_BACKSLASH:
                    self.debug_text = ""
                    self.game_state = GameState.DEBUG

        # Draw screen:
        self.game.draw_action()

    def game_over_state(self):
        # Sprite group updates:
        self.game.update_sprites()

        # Check collisions:
        self.game.check_projectile_hits(self.game.spaceship.weapons.projectiles)

        # Kill sprites outside of screen:
        self.game.kill_all_offbound_sprites()
        # Draw screen:
        self.game.draw_action()

        txt = self.game.title_font.render("YOU'RE DEAD !!!!", False, pygame.Color('chartreuse3'))
        rect = txt.get_rect(center=(self.game.width / 2, self.game.height / 2))
        self.game.window.blit(txt, rect)

    def pause_state(self):
        self.game.draw_action(add_scroll=False)
        txt = self.game.title_font.render("PAUSED ", False, pygame.Color('chartreuse3'))
        rect = txt.get_rect(center=(self.game.width / 2, self.game.height / 2))
        self.game.window.blit(txt, rect)

        for event in pygame.event.get():
            # Events:
            self.game.process_event(event)
            # Unpause:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.game_state = GameState.RUNNING

    def debug_state(self):
        self.game.draw_action(add_scroll=False)
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.game_state = GameState.QUIT
                case pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_BACKSLASH:
                        self.game.parse_debug_code(self.debug_text)
                        self.game_state = GameState.RUNNING
                    elif event.key == pygame.K_BACKSPACE:
                        self.debug_text = self.debug_text[:-1]
                    else:
                        self.debug_text += event.unicode

        txt = self.game.status_font.render(f">{self.debug_text}", False, pygame.Color('white'))
        rect = txt.get_rect(topleft=(600, 200))
        self.window.blit(txt, rect)


class Background:
    def __init__(self, window):
        self.planets = pygame.sprite.Group()
        pygame.time.set_timer(PLANET_EVENT, 45000)

        self.bg = [pygame.image.load(f'assets/bg/bkgd_{idx}.png').convert_alpha() for idx in [1, 2, 3, 5, 7]]
        self.bg_width = self.bg[0].get_width()
        self.scroll = [0] * 8
        self.tiles = math.ceil(window.get_width() / self.bg_width) + 1
        self.window = window
        self.width = self.window.get_width()
        self.height = self.window.get_height()

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

    def spawn_planet(self):
        size = random.randint(200, 500)
        if random.random() > 0.5:
            y = random.randint(round(-size / 4), 0)
        else:
            y = random.randint(self.height, self.height + round(size / 4))

        model = random.randint(1, 16)
        rotation = random.randint(0, 360)
        image = scale_and_rotate(f"assets/Sprites/Planets/planet-{model}.png", rotate=rotation,
                                 size=(size, size))

        planet = Planet(image, self.width + size // 2, y, size)
        self.planets.add(planet)
