import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PLAYER_SPEED = 5
HEART_SPEED = 5
BULLET_SPEED_MIN, BULLET_SPEED_MAX = 2, 5
PLAYER_BULLET_SPEED = 5
FPS = 60
PLAYER_MAX_HP = 20
ENEMY_BULLET_DAMAGE = 2

# Battle box dimensions and position (wide rectangle, shifted down)
BOX_WIDTH, BOX_HEIGHT = 400, 200
BOX_X = (WIDTH - BOX_WIDTH) // 2
BOX_Y = (HEIGHT - BOX_HEIGHT) // 2 + 50  # Shifted down by 50 pixels

# Dialogue box dimensions and position (wider, adjusted for new battle box position)
DIALOGUE_WIDTH, DIALOGUE_HEIGHT = 700, 50  # Width 700
DIALOGUE_X = (WIDTH - DIALOGUE_WIDTH) // 2
DIALOGUE_Y = BOX_Y + BOX_HEIGHT + 30  # Below health bar

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Undertale Clone by Daksh Joshi")

# Load and scale assets
background = pygame.image.load("background.jpg").convert()  # 800x600 JPG
player_img = pygame.transform.scale(pygame.image.load("player.jpg").convert(), (144, 144))  # ~1.5 inch JPG
heart_img = pygame.transform.scale(pygame.image.load("heart.png").convert_alpha(), (48, 48))  # ~0.5 inch PNG
bullet_img = pygame.transform.scale(pygame.image.load("bullet.png").convert_alpha(), (20, 20))  # ~0.2 inch PNG
enemy_imgs = [
    pygame.transform.scale(pygame.image.load("enemy1.png").convert_alpha(), (144, 144)),  # Frog
    pygame.transform.scale(pygame.image.load("enemy2.png").convert_alpha(), (144, 144)),  # Bat
    pygame.transform.scale(pygame.image.load("enemy3.png").convert_alpha(), (144, 144))   # Flower
]

# Initial positions and states
player_x, player_y = WIDTH // 2 - 72, HEIGHT // 2 - 72  # Center 144x144 sprite
heart_x, heart_y = WIDTH // 2 - 24, HEIGHT // 2 - 24    # Center 48x48 sprite
heart_speed_x, heart_speed_y = 0, 0
player_hp = PLAYER_MAX_HP
battle_mode = False
enemy_bullets = []
player_bullets = []
game_started = False
paused = False
battle_won = False
dialogue_text = ""
dialogue_timer = 0  # Frames to display dialogue (2 seconds = 120 frames at 60 FPS)

# Enemy properties (adjusted y positions)
enemies = [
    {"x": WIDTH // 2, "y": 150, "speed_x": 2, "img": enemy_imgs[0], "hp": 30, "max_hp": 30, "firing": True, "bullet_count": 0, "wait_timer": 0},  # Frog
    {"x": WIDTH // 2, "y": 130, "speed_x": 3, "img": enemy_imgs[1], "hp": 22, "max_hp": 22, "firing": True, "bullet_count": 0, "wait_timer": 0},  # Bat
    {"x": WIDTH // 2, "y": 170, "speed_x": 1.5, "img": enemy_imgs[2], "hp": 25, "max_hp": 25, "firing": True, "bullet_count": 0, "wait_timer": 0}  # Flower
]
current_enemy_index = 0
enemy_active = False

# Fonts
try:
    title_font = pygame.font.Font("PressStart2P-Regular.ttf", 40)
    small_font = pygame.font.Font("PressStart2P-Regular.ttf", 24)
    dialogue_font = pygame.font.Font("PressStart2P-Regular.ttf", 20)
except:
    title_font = pygame.font.SysFont("Arial", 40, bold=True)
    small_font = pygame.font.SysFont("Arial", 24, bold=True)
    dialogue_font = pygame.font.SysFont("Arial", 20, bold=True)

# Functions
def reset_game():
    """Reset all game states for a new battle."""
    global player_hp, battle_mode, enemy_active, current_enemy_index, enemy_bullets, player_bullets, battle_won, dialogue_text, dialogue_timer
    player_hp = PLAYER_MAX_HP
    battle_mode = True
    enemy_active = True
    current_enemy_index = 0
    enemy_bullets.clear()
    player_bullets.clear()
    battle_won = False
    dialogue_text = ""
    dialogue_timer = 0
    reset_enemies()
    heart_x, heart_y = WIDTH // 2 - 24, HEIGHT // 2 - 24

def reset_enemies():
    """Reset all enemy states."""
    for i, enemy in enumerate(enemies):
        enemy["hp"] = enemy["max_hp"]
        enemy["firing"] = True
        enemy["bullet_count"] = 0
        enemy["wait_timer"] = 0
        enemy["x"] = WIDTH // 2
        if i == 0:
            enemy["y"] = 150  # Frog
        elif i == 1:
            enemy["y"] = 130  # Bat
        elif i == 2:
            enemy["y"] = 170  # Flower

def set_dialogue(message):
    """Set dialogue text and reset timer."""
    global dialogue_text, dialogue_timer
    dialogue_text = message
    dialogue_timer = 120  # 2 seconds at 60 FPS

def handle_player_movement(keys, x, y, speed):
    """Move player with arrow keys."""
    if keys[pygame.K_LEFT]:
        x -= speed
    if keys[pygame.K_RIGHT]:
        x += speed
    if keys[pygame.K_UP]:
        y -= speed
    if keys[pygame.K_DOWN]:
        y += speed
    x = max(0, min(x, WIDTH - 144))
    y = max(0, min(y, HEIGHT - 144))
    return x, y

def handle_heart_movement(event):
    """Move heart with WASD keys."""
    global heart_speed_x, heart_speed_y
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_a:
            heart_speed_x = -HEART_SPEED
        elif event.key == pygame.K_d:
            heart_speed_x = HEART_SPEED
        elif event.key == pygame.K_w:
            heart_speed_y = -HEART_SPEED
        elif event.key == pygame.K_s:
            heart_speed_y = HEART_SPEED
    elif event.type == pygame.KEYUP:
        if event.key in (pygame.K_a, pygame.K_d):
            heart_speed_x = 0
        if event.key in (pygame.K_w, pygame.K_s):
            heart_speed_y = 0

def constrain_heart(x, y):
    """Keep heart within the wider battle box."""
    x = max(BOX_X + 24, min(x, BOX_X + BOX_WIDTH - 24))
    y = max(BOX_Y + 24, min(y, BOX_Y + BOX_HEIGHT - 24))
    return x, y

def spawn_enemy_bullet(enemy_x, enemy_y):
    """Spawn an enemy bullet with random direction and speed."""
    angle = random.uniform(-math.pi / 4, math.pi / 4)
    speed = random.uniform(BULLET_SPEED_MIN, BULLET_SPEED_MAX)
    speed_x = math.sin(angle) * speed
    speed_y = math.cos(angle) * speed
    return {"x": enemy_x + 72, "y": enemy_y + 144, "speed_x": speed_x, "speed_y": speed_y}

def spawn_player_bullet(heart_x, heart_y):
    """Spawn a player bullet upward."""
    return {"x": heart_x, "y": heart_y - 24, "speed_x": 0, "speed_y": -PLAYER_BULLET_SPEED}

def update_bullets():
    """Update all bullets and remove off-screen ones."""
    for bullet in enemy_bullets[:]:
        bullet["x"] += bullet["speed_x"]
        bullet["y"] += bullet["speed_y"]
        if bullet["y"] > HEIGHT or bullet["x"] < 0 or bullet["x"] > WIDTH or bullet["y"] < 0:
            enemy_bullets.remove(bullet)
    for bullet in player_bullets[:]:
        bullet["x"] += bullet["speed_x"]
        bullet["y"] += bullet["speed_y"]
        if bullet["y"] < 0:
            player_bullets.remove(bullet)

def update_enemy(enemy):
    """Move enemy horizontally and bounce off screen edges."""
    enemy["x"] += enemy["speed_x"]
    if enemy["x"] - 72 < 0 or enemy["x"] + 72 > WIDTH:
        enemy["speed_x"] = -enemy["speed_x"]
    enemy["x"] = max(72, min(enemy["x"], WIDTH - 72))

def check_enemy_collision(enemy):
    """Check if player bullets hit the enemy, dealing 5-10 damage."""
    enemy_rect = pygame.Rect(enemy["x"] - 72, enemy["y"] - 72, 144, 144)
    for bullet in player_bullets[:]:
        bullet_rect = pygame.Rect(bullet["x"] - 10, bullet["y"] - 10, 20, 20)
        if enemy_rect.colliderect(bullet_rect):
            damage = random.randint(5, 10)
            enemy["hp"] -= damage
            player_bullets.remove(bullet)
            set_dialogue(f"Enemy hit! Dealt {damage} damage. HP: {enemy['hp']}")
            return enemy["hp"] <= 0
    return False

def check_heart_collision():
    """Check if heart collides with enemy bullets and reduce HP."""
    global player_hp
    heart_rect = pygame.Rect(heart_x - 24, heart_y - 24, 48, 48)
    for bullet in enemy_bullets[:]:
        bullet_rect = pygame.Rect(bullet["x"] - 10, bullet["y"] - 10, 20, 20)
        if heart_rect.colliderect(bullet_rect):
            player_hp -= ENEMY_BULLET_DAMAGE
            enemy_bullets.remove(bullet)
            set_dialogue(f"Heart hit! HP remaining: {player_hp}")
            return player_hp <= 0
    return False

def draw_battle_box():
    """Draw the wider battle box outline."""
    pygame.draw.rect(screen, BLACK, (BOX_X, BOX_Y, BOX_WIDTH, BOX_HEIGHT), 2)

def draw_health_bar(enemy):
    """Draw a green health bar above the enemy."""
    health_width = 100 * (enemy["hp"] / enemy["max_hp"])
    pygame.draw.rect(screen, BLACK, (enemy["x"] - 50, enemy["y"] - 90, 100, 10))  # Background
    pygame.draw.rect(screen, GREEN, (enemy["x"] - 50, enemy["y"] - 90, health_width, 10))  # Health

def draw_player_health_bar():
    """Draw a green health bar for the player below the battle box."""
    health_width = 200 * (player_hp / PLAYER_MAX_HP)
    pygame.draw.rect(screen, BLACK, (BOX_X, BOX_Y + BOX_HEIGHT + 10, 200, 10))  # Background
    pygame.draw.rect(screen, GREEN, (BOX_X, BOX_Y + BOX_HEIGHT + 10, health_width, 10))  # Health

def draw_dialogue_box():
    """Draw the wider dialogue box with yellow pixelated text."""
    global dialogue_timer
    if dialogue_timer > 0:
        pygame.draw.rect(screen, BLACK, (DIALOGUE_X, DIALOGUE_Y, DIALOGUE_WIDTH, DIALOGUE_HEIGHT))  # Background
        pygame.draw.rect(screen, WHITE, (DIALOGUE_X, DIALOGUE_Y, DIALOGUE_WIDTH, DIALOGUE_HEIGHT), 2)  # Border
        text = dialogue_font.render(dialogue_text, True, YELLOW)
        screen.blit(text, (DIALOGUE_X + 10, DIALOGUE_Y + (DIALOGUE_HEIGHT - text.get_height()) // 2))  # Centered vertically
        dialogue_timer -= 1

def draw_start_menu():
    """Draw the start menu with bold, pixelated, yellow text."""
    screen.blit(background, (0, 0))
    title_text = title_font.render("Press SPACE to Play", True, YELLOW)
    credit_text = small_font.render("Made by Daksh Joshi", True, YELLOW)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - title_text.get_height() // 2))
    screen.blit(credit_text, (WIDTH - credit_text.get_width() - 10, HEIGHT - credit_text.get_height() - 10))

def draw_pause_screen():
    """Draw the pause overlay."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    pause_text = title_font.render("Paused (Press P)", True, YELLOW)
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

def draw_win_screen():
    """Draw the win screen with yellow pixelated text."""
    screen.blit(background, (0, 0))
    win_text = title_font.render("YOU WON", True, YELLOW)
    retry_text = small_font.render("Press SPACE to Retry", True, YELLOW)
    screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - win_text.get_height() - 20))
    screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 20))

# Game loop
clock = pygame.time.Clock()
bullet_timer = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if not game_started and event.key == pygame.K_SPACE:
                game_started = True
            elif game_started and event.key == pygame.K_p and not battle_won:
                paused = not paused
            elif game_started and event.key == pygame.K_b and not paused and not battle_won:
                battle_mode = not battle_mode
                enemy_active = battle_mode
                enemy_bullets.clear()
                player_bullets.clear()
                heart_x, heart_y = WIDTH // 2 - 24, HEIGHT // 2 - 24
                current_enemy_index = 0
                player_hp = PLAYER_MAX_HP
                if battle_mode:
                    reset_enemies()
            elif battle_mode and not paused and not battle_won and event.key == pygame.K_SPACE:
                player_bullets.append(spawn_player_bullet(heart_x, heart_y))
            elif battle_won and event.key == pygame.K_SPACE:
                reset_game()
        if battle_mode and not paused and not battle_won:
            handle_heart_movement(event)

    if not game_started:
        draw_start_menu()
    elif paused:
        draw_pause_screen()
    elif battle_won:
        draw_win_screen()
    else:
        # Update game state
        keys = pygame.key.get_pressed()
        if not battle_mode:
            player_x, player_y = handle_player_movement(keys, player_x, player_y, PLAYER_SPEED)
        else:
            if not paused and not battle_won:
                heart_x += heart_speed_x
                heart_y += heart_speed_y
                heart_x, heart_y = constrain_heart(heart_x, heart_y)

                if enemy_active and current_enemy_index < len(enemies):
                    current_enemy = enemies[current_enemy_index]
                    update_enemy(current_enemy)
                    if current_enemy["hp"] > 0:
                        if current_enemy["firing"]:
                            bullet_timer += 1
                            if bullet_timer >= 10 and current_enemy["bullet_count"] < 8:
                                enemy_bullets.append(spawn_enemy_bullet(current_enemy["x"], current_enemy["y"]))
                                current_enemy["bullet_count"] += 1
                                bullet_timer = 0
                            if current_enemy["bullet_count"] >= 8:
                                current_enemy["firing"] = False
                                current_enemy["wait_timer"] = 300
                        else:
                            current_enemy["wait_timer"] -= 1
                            if current_enemy["wait_timer"] <= 0:
                                current_enemy["firing"] = True
                                current_enemy["bullet_count"] = 0

                    update_bullets()

                    if check_enemy_collision(current_enemy):
                        if current_enemy["hp"] <= 0:
                            set_dialogue(f"Enemy {current_enemy_index + 1} defeated!")
                            current_enemy_index += 1
                            if current_enemy_index >= len(enemies):
                                battle_won = True
                                enemy_active = False
                                battle_mode = False
                            else:
                                enemies[current_enemy_index]["firing"] = True
                                enemies[current_enemy_index]["bullet_count"] = 0
                                enemies[current_enemy_index]["wait_timer"] = 0
                            enemy_bullets.clear()
                            player_bullets.clear()

                    if check_heart_collision():
                        if player_hp <= 0:
                            set_dialogue("Player HP depleted! Game over!")
                            battle_mode = False
                            enemy_active = False
                        enemy_bullets.clear()
                        player_bullets.clear()

        # Draw everything
        screen.blit(background, (0, 0))
        if not battle_mode and not battle_won:
            screen.blit(player_img, (player_x, player_y))
        elif not battle_won:
            draw_battle_box()
            screen.blit(heart_img, (heart_x - 24, heart_y - 24))
            draw_player_health_bar()
            if enemy_active and current_enemy_index < len(enemies):
                current_enemy = enemies[current_enemy_index]
                if current_enemy["hp"] > 0:
                    screen.blit(current_enemy["img"], (current_enemy["x"] - 72, current_enemy["y"] - 72))
                    draw_health_bar(current_enemy)
                for bullet in enemy_bullets:
                    screen.blit(bullet_img, (int(bullet["x"] - 10), int(bullet["y"] - 10)))
                for bullet in player_bullets:
                    screen.blit(bullet_img, (int(bullet["x"] - 10), int(bullet["y"] - 10)))
            draw_dialogue_box()

    # Update display
    pygame.display.flip()
    clock.tick(FPS)