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

playerX = 400
playerY = 500
player_speed = 0
acceleration = 0.002
max_speed = 0.5
friction = 0.001
reverse_speed = -0.2
angle = 0
rotation_speed = 0.3

# Generate the track
track_points = generate_track(WIDTH, HEIGHT)

def player(x, y, angle):
    rotated_image = pygame.transform.rotate(playerImg, angle)
    new_rect = rotated_image.get_rect(center=(x + new_width // 2, y + new_height // 2))
    screen.blit(rotated_image, new_rect.topleft)

running = True
while running:
    screen.fill((0, 200, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_track(screen, track_points, TRACK_WIDTH)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        if player_speed < 0:
            player_speed += friction
        else:
            player_speed += acceleration
            if player_speed > max_speed:
                player_speed = max_speed

    elif keys[pygame.K_DOWN]:
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

    if player_speed != 0:
        if keys[pygame.K_LEFT]:
            angle += rotation_speed
        if keys[pygame.K_RIGHT]:
            angle -= rotation_speed

    playerX += player_speed * math.cos(math.radians(-angle))
    playerY += player_speed * math.sin(math.radians(-angle))

    player(playerX, playerY, angle)
    pygame.display.update()
