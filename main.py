import os
import random
import pygame
from pygame.locals import *
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
BULLET_SPEED = 7
ALIEN_SPEED_START = 1
ALIEN_SPEED_INCREMENT = 0.1
BUTTON_COLOR = (0, 0, 255)
BUTTON_HOVER_COLOR = (0, 0, 200)
BUTTON_TEXT_COLOR = (255, 255, 255)
FONT_SIZE = 36
BUTTON_FONT_SIZE = 24

# Load resources
PLAYER_IMG = os.getenv("PLAYER_IMG", None)
ALIEN_IMGS = [
    os.getenv("ALIEN_IMG_1", None),
    os.getenv("ALIEN_IMG_2", None),
    os.getenv("ALIEN_IMG_3", None),
    os.getenv("ALIEN_IMG_4", None)
]
SHOOT_SOUND = os.getenv("SHOOT_SOUND", None)
HIT_SOUND = os.getenv("HIT_SOUND", None)
COLLISION_SOUND = os.getenv("COLLISION_SOUND", None)

# Button image paths
START_BUTTON_IMG = os.getenv("START_BUTTON_IMG", None)
PAUSE_BUTTON_IMG = os.getenv("PAUSE_BUTTON_IMG", None)
CONTINUE_BUTTON_IMG = os.getenv("CONTINUE_BUTTON_IMG", None)
RESTART_BUTTON_IMG = os.getenv("RESTART_BUTTON_IMG", None)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Alien Invasion')
clock = pygame.time.Clock()
font = pygame.font.Font(None, FONT_SIZE)
button_font = pygame.font.Font(None, BUTTON_FONT_SIZE)

# Load assets with fallbacks
def load_image(path, fallback_color):
    try:
        image = pygame.image.load(path)
    except:
        image = pygame.Surface((50, 50))
        image.fill(fallback_color)
    return image

def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        return None

player_image = load_image(PLAYER_IMG, (0, 255, 0))
alien_images = [load_image(img, (255, 0, 0)) for img in ALIEN_IMGS]
shoot_sound = load_sound(SHOOT_SOUND)
hit_sound = load_sound(HIT_SOUND)
collision_sound = load_sound(COLLISION_SOUND)

# Load button images with fallbacks
def load_button_image(path, width, height):
    if path and os.path.exists(path):
        return pygame.transform.scale(pygame.image.load(path), (width, height))
    else:
        return None

start_button_image = load_button_image(START_BUTTON_IMG, 100, 50)
pause_button_image = load_button_image(PAUSE_BUTTON_IMG, 100, 50)
continue_button_image = load_button_image(CONTINUE_BUTTON_IMG, 100, 50)
restart_button_image = load_button_image(RESTART_BUTTON_IMG, 100, 50)

# Game classes
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_image
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = PLAYER_SPEED
        self.bullets = pygame.sprite.Group()
        self.shooting = False

    def update(self, keys):
        if keys[K_LEFT]:
            self.rect.x -= self.speed
        if keys[K_RIGHT]:
            self.rect.x += self.speed
        if keys[K_UP]:
            self.rect.y -= self.speed
        if keys[K_DOWN]:
            self.rect.y += self.speed

        # Keep player on the screen
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, SCREEN_WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, SCREEN_HEIGHT)

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        self.bullets.add(bullet)
        if shoot_sound:
            shoot_sound.play()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed = BULLET_SPEED

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class Alien(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = random.choice(alien_images)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-100, -40)
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Button:
    def __init__(self, text, x, y, width, height, callback, image=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER_COLOR
        self.text_color = BUTTON_TEXT_COLOR
        self.font = button_font
        self.callback = callback
        self.hovered = False
        self.clicked = False
        self.image = image

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()

        if self.rect.collidepoint(mouse_pos):
            self.hovered = True
            if mouse_click[0] == 1 and not self.clicked:
                self.callback()
                self.clicked = True
        else:
            self.hovered = False

        if not mouse_click[0]:
            self.clicked = False

        if self.image:
            screen.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(screen, self.hover_color if self.hovered else self.color, self.rect)
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

class Game:
    def __init__(self):
        self.player = Player()
        self.aliens = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.score = 0
        self.alien_speed = ALIEN_SPEED_START
        self.spawn_timer = 0
        self.paused = False
        self.game_over_flag = False
        self.game_started = False

        self.start_button = Button('Start', 10, 10, 100, 50, self.start_game, start_button_image)
        self.pause_button = Button('Pause', 120, 10, 100, 50, self.pause_game, pause_button_image)
        self.continue_button = Button('Continue', 120, 10, 100, 50, self.pause_game, continue_button_image)
        self.restart_button = Button('Restart', 230, 10, 100, 50, self.restart_game, restart_button_image)

    def start_game(self):
        self.paused = False
        self.game_started = True
        self.start_button = None  # Remove start button after game starts

    def pause_game(self):
        self.paused = not self.paused

    def restart_game(self):
        self.__init__()
        self.start_game()

    def spawn_alien(self):
        alien = Alien(self.alien_speed)
        self.aliens.add(alien)
        self.all_sprites.add(alien)

    def update(self):
        if self.game_started and not self.paused and not self.game_over_flag:
            keys = pygame.key.get_pressed()
            self.player.update(keys)
            self.player.bullets.update()
            self.aliens.update()

            for bullet in self.player.bullets:
                hits = pygame.sprite.spritecollide(bullet, self.aliens, True)
                for hit in hits:
                    bullet.kill()
                    self.score += 10
                    if hit_sound:
                        hit_sound.play()

            if pygame.sprite.spritecollide(self.player, self.aliens, True):
                if collision_sound:
                    collision_sound.play()
                self.game_over()

            self.spawn_timer += 1
            if self.spawn_timer >= 50:
                self.spawn_alien()
                self.spawn_timer = 0

            self.alien_speed += ALIEN_SPEED_INCREMENT / 1000

    def draw(self):
        screen.fill((0, 0, 0))
        self.all_sprites.draw(screen)
        self.player.bullets.draw(screen)
        self.draw_text(f'Score: {self.score}', 25, SCREEN_WIDTH // 2, 10)

        if self.start_button:
            self.start_button.draw(screen)
        if self.game_started:
            if self.paused:
                self.continue_button.draw(screen)
            else:
                self.pause_button.draw(screen)
            self.restart_button.draw(screen)

        if not self.game_started:
            self.draw_text('Press Start to Play', 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        elif self.paused:
            self.draw_text('Paused', 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        elif self.game_over_flag:
            self.draw_text('Game Over', 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
            self.draw_text(f'Your score: {self.score}', 36, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)

    def draw_text(self, text, size, x, y):
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        screen.blit(text_surface, text_rect)

    def game_over(self):
        self.game_over_flag = True

# Main game loop
def main():
    game = Game()
    running = True
    last_shoot_time = 0
    shoot_delay = 250  # milliseconds

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    game.player.shooting = True
            elif event.type == KEYUP:
                if event.key == K_SPACE:
                    game.player.shooting = False

        current_time = pygame.time.get_ticks()
        if game.player.shooting and current_time - last_shoot_time > shoot_delay:
            game.player.shoot()
            last_shoot_time = current_time

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
