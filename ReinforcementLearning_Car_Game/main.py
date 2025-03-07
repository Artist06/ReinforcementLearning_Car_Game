import pygame
import math
from track import generate_track, draw_track, TRACK_WIDTH

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Track Invaders")

icon = pygame.image.load('racing.png')
pygame.display.set_icon(icon)

playerImg = pygame.image.load('racing-car.png')
new_width = 48
new_height = int((new_width / playerImg.get_width()) * playerImg.get_height())
playerImg = pygame.transform.scale(playerImg, (new_width, new_height))

steering_wheel_img = pygame.image.load('images/steering-wheel.png')
steering_wheel_img = pygame.transform.scale(steering_wheel_img, (150, 150))

pedal_size = (80, 80)
accelerator_img = pygame.transform.scale(pygame.image.load('brake.png'), pedal_size)
brake_img = pygame.transform.scale(pygame.image.load('accelerator.png'), pedal_size)

accelerator_rect = accelerator_img.get_rect(bottomleft=(50, HEIGHT - 20))
brake_rect = brake_img.get_rect(bottomleft=(150, HEIGHT - 20))

track_points = generate_track(WIDTH, HEIGHT)

playerX, playerY = track_points[0]
angle = math.degrees(math.atan2(track_points[1][1] - playerY, track_points[1][0] - playerX))

player_speed = 0
acceleration = 0.005
max_speed = 0.7
friction = 0.005
reverse_speed = -0.3
rotation_speed = 0.8

steering_angle = 0
steering_sensitivity = 4
steering_return_speed = 2

clock = pygame.time.Clock()

def player(x, y, angle):
    rotated_image = pygame.transform.rotate(playerImg, angle)
    new_rect = rotated_image.get_rect(center=(x + new_width // 2, y + new_height // 2))
    screen.blit(rotated_image, new_rect.topleft)

def draw_steering_wheel():
    rotated_wheel = pygame.transform.rotate(steering_wheel_img, -steering_angle)
    wheel_rect = rotated_wheel.get_rect(center=(WIDTH - 100, HEIGHT - 100))
    screen.blit(rotated_wheel, wheel_rect.topleft)

def draw_pedals(accelerating, braking):
    if accelerating:
        scaled_accel = pygame.transform.scale(accelerator_img, (pedal_size[0] - 10, pedal_size[1] - 10))
        screen.blit(scaled_accel, accelerator_rect.topleft)
    else:
        screen.blit(accelerator_img, accelerator_rect.topleft)

    if braking:
        scaled_brake = pygame.transform.scale(brake_img, (pedal_size[0] - 10, pedal_size[1] - 10))
        screen.blit(scaled_brake, brake_rect.topleft)
    else:
        screen.blit(brake_img, brake_rect.topleft)

running = True
while running:
    screen.fill((0, 190, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_track(screen, track_points, TRACK_WIDTH)

    keys = pygame.key.get_pressed()
    accelerating = keys[pygame.K_UP]
    braking = keys[pygame.K_DOWN]

    if accelerating:
        if player_speed < 0:
            player_speed += friction
        else:
            player_speed += acceleration
            if player_speed > max_speed:
                player_speed = max_speed
    elif braking:
        if player_speed > 0:
            player_speed -= friction
        else:
            player_speed -= acceleration
            if player_speed < reverse_speed:
                player_speed = reverse_speed
    else:
        if player_speed > 0:
            player_speed -= friction
        elif player_speed < 0:
            player_speed += friction
        if abs(player_speed) < friction:
            player_speed = 0

    if player_speed != 0:  # Rotation only when moving
        direction = 1 if player_speed > 0 else -1  # Reverse rotation when moving backward
        if keys[pygame.K_LEFT]:
            angle += rotation_speed * direction
        if keys[pygame.K_RIGHT]:
            angle -= rotation_speed * direction

    if keys[pygame.K_LEFT]:
        steering_angle = max(steering_angle - steering_sensitivity, -30)
    if keys[pygame.K_RIGHT]:
        steering_angle = min(steering_angle + steering_sensitivity, 30)

    if not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
        if steering_angle > 0:
            steering_angle = max(steering_angle - steering_return_speed, 0)
        elif steering_angle < 0:
            steering_angle = min(steering_angle + steering_return_speed, 0)

    playerX += player_speed * math.cos(math.radians(-angle))
    playerY += player_speed * math.sin(math.radians(-angle))

    player(playerX, playerY, angle)
    draw_steering_wheel()
    draw_pedals(accelerating, braking)

    fps = int(clock.get_fps())
    font = pygame.font.SysFont(None, 30)
    fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
    screen.blit(fps_text, (10, 10))

    pygame.display.update()
    clock.tick()
