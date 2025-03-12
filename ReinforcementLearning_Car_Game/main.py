import pygame
import math
import random
from pygame import mixer
from track import draw_track, TRACK_WIDTH, catmull_rom_chain, generate_track

pygame.init()
mixer.init()

NUM_POINTS = 100
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Track Invaders")

icon = pygame.image.load('images/racing.png')
pygame.display.set_icon(icon)

playerImg = pygame.image.load('images/racing-car.png')
new_width = 48
new_height = int((new_width / playerImg.get_width()) * playerImg.get_height())
playerImg = pygame.transform.scale(playerImg, (new_width, new_height))

steering_wheel_img = pygame.image.load('images/steering-wheel.png')
steering_wheel_img = pygame.transform.scale(steering_wheel_img, (150, 150))

pedal_size = (80, 80)
accelerator_img = pygame.transform.scale(pygame.image.load('images/brake.png'), pedal_size)
brake_img = pygame.transform.scale(pygame.image.load('images/accelerator.png'), pedal_size)

accelerator_rect = accelerator_img.get_rect(bottomleft=(50, HEIGHT - 20))
brake_rect = brake_img.get_rect(bottomleft=(150, HEIGHT - 20))

tree_img = pygame.image.load('images/grass.png')
tree_size = (50, 50)
tree_img = pygame.transform.scale(tree_img, tree_size)

font = pygame.font.SysFont(None, 50)

# Menu options
menu_options = ["Start Game", "Rules", "Exit"]
current_option = 0

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)

def main_menu():
    global current_option
    menu_running = True
    mixer.music.load("sounds/menu_background.wav")
    mixer.music.play(-1)        #menu background starts playing
    while menu_running:
        screen.fill((15, 70, 8))

        for i, option in enumerate(menu_options):
            color = (255, 255, 255) if i == current_option else (100, 100, 100)
            draw_text(option, font, color, screen, WIDTH // 2, HEIGHT // 2 - 100 + i * 60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                return "Exit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_running = False
                    mixer.music.stop()  #menu background stops
                    return "Exit"
                if event.key == pygame.K_UP:
                    current_option = (current_option - 1) % len(menu_options)
                if event.key == pygame.K_DOWN:
                    current_option = (current_option + 1) % len(menu_options)
                if event.key == pygame.K_RETURN:
                    if menu_options[current_option] == "Start Game":
                        mixer.music.stop()  #menu background stops
                        return "Start Game"
                    elif menu_options[current_option] == "Rules":
                        rule_return = rules_menu()
                        if rule_return == "Exit":
                            menu_running = False
                            mixer.music.stop()  #menu background stops
                            return "Exit"
                    elif menu_options[current_option] == "Exit":
                        menu_running = False
                        mixer.music.stop()   #menu background stops
                        return "Exit"

        pygame.display.update()

def rules_menu():
    rules_running = True
    font_small = pygame.font.SysFont(None, 36)
    rules = [
        "Rules:",
        "Use arrow keys to control the car:",
        " - UP: Accelerate",
        " - DOWN: Brake/Reverse",
        " - LEFT: Steer left",
        " - RIGHT: Steer right",
        "Stay on the grey track. Going outside results in Game Over.",
        "Press ESC to go back to the main menu."
    ]

    while rules_running:
        screen.fill((10, 55, 20))

        for i, line in enumerate(rules):
            draw_text(line, font_small, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2 - 150 + i * 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rules_running = False
                return "Exit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    rules_running = False

        pygame.display.update()

def generate_tree_positions(num_trees, outer_points, tree_size, min_distance):
    tree_positions = []
    control_areas = [(WIDTH - 150, HEIGHT - 150, 100, 100),  # Steering wheel area
                     (0, HEIGHT - 100, 100, 100),  # Accelerator area
                     (150, HEIGHT - 100, 100, 100)]  # Brake area

    while len(tree_positions) < num_trees:
        tree_x = random.randint(0, WIDTH - tree_size[0])
        tree_y = random.randint(0, HEIGHT - tree_size[1])

        # Check if the tree is outside the track and controls
        on_track_or_controls = False
        for outer_point in outer_points:
            distance = math.sqrt((tree_x - outer_point[0]) ** 2 + (tree_y - outer_point[1]) ** 2)
            if distance < TRACK_WIDTH:
                on_track_or_controls = True
                break
        for area in control_areas:
            if area[0] <= tree_x <= area[0] + area[2] and area[1] <= tree_y <= area[1] + area[3]:
                on_track_or_controls = True
                break

        if not on_track_or_controls:
            too_close = False
            for pos in tree_positions:
                if math.sqrt((tree_x - pos[0]) ** 2 + (tree_y - pos[1]) ** 2) < min_distance:
                    too_close = True
                    break
            if not too_close:
                tree_positions.append((tree_x, tree_y))

    return tree_positions

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

def is_within_track(car_rect, inner_points, outer_points):
    def get_distance(point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    for i in range(len(inner_points) - 1):
        inner_dist = get_distance(car_rect.center, inner_points[i])
        outer_dist = get_distance(car_rect.center, outer_points[i])
        if inner_dist < TRACK_WIDTH and outer_dist < TRACK_WIDTH:
            return True

    return False

def game_loop():
    font_size = 30
    font = pygame.font.Font(None, font_size)
    global playerX, playerY, angle, player_speed, steering_angle, distance_covered, track_points, curve_points, outer_points, inner_points, num_trees

    track_points = []
    for i in range(6):
        if i < 6 // 2:
            track_points.append((random.randint(40 + (i % 3) * 240, 40 + ((i % 3) + 1) * 240),
                                 40 + random.randint((i // 3) * 250, ((i // 3) + 1) * 250)))
        else:
            track_points.append((random.randint(40 + (2 - (i % 3)) * 240, 40 + (3 - (i % 3)) * 240),
                                 50 + random.randint((i // 3) * 250, ((i // 3) + 1) * 250)))

    for i in range(6 // 2):
        track_points.append(track_points[i])

    curve_points = catmull_rom_chain(track_points, NUM_POINTS)
    outer_points, inner_points = generate_track(curve_points, TRACK_WIDTH)

    playerX, playerY = curve_points[0]
    angle = math.degrees(math.atan2(curve_points[1][1] - playerY, curve_points[1][0] - playerX))

    player_speed = 0
    acceleration = 0.005
    max_speed = 0.7
    friction = 0.005
    reverse_speed = -0.3
    rotation_speed = 0.8

    steering_angle = 0
    steering_sensitivity = 4
    steering_return_speed = 2
    distance_covered = 0

    tree_positions = generate_tree_positions(10, outer_points, tree_size, min_distance=100)

    clock = pygame.time.Clock()
    running = True
    game_over = False
    play_once_over = True
    engine_start_once = True
    engine_event = pygame.USEREVENT + 1         #delay for engine sound
    pygame.time.set_timer(engine_event, 2000)
    
    #loading sounds
    engine_sound=mixer.Sound("sounds/engine.mp3")
    engine_start_sound=mixer.Sound("sounds/engine_start.wav")
    game_over_sound=mixer.Sound("sounds/game-over.mp3")

    while running:
        screen.fill((0, 170, 0))
        if engine_start_once:               #engine starts once
            engine_start_sound.play()
            engine_start_once = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == engine_event:      #engine sound starts playing
                engine_sound.play(-1)

        if not game_over:
            draw_track(screen, outer_points, inner_points, curve_points, TRACK_WIDTH)

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

            if player_speed > 0:  # Moving forward
                distance_covered += player_speed
            elif player_speed < 0:  # Moving backward
                if(distance_covered>=0):
                    distance_covered += player_speed
                else:
                    distance_covered = 0
                    
            score_text = font.render(f"Score: {int(distance_covered/10)}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH - 200, 15))

            rotated_image = pygame.transform.rotate(playerImg, angle)
            player_rect = rotated_image.get_rect(center=(playerX + new_width // 2, playerY + new_height // 2))

            # Check if the car is outside the track
            if not is_within_track(player_rect, inner_points, outer_points):
                game_over = True

            # Prevent player from going out of bounds
            playerX = max(0, min(WIDTH - new_width, playerX))
            playerY = max(0, min(HEIGHT - new_height, playerY))

            player(playerX, playerY, angle)
            draw_steering_wheel()
            draw_pedals(accelerating, braking)

            for tree_pos in tree_positions:
                screen.blit(tree_img, tree_pos)
        else:
            engine_sound.stop()     #engine sound stops
            if play_once_over:      #game over sound plays once
                game_over_sound.play()
                play_once_over = False
            game_over_text = font.render("Game Over", True, (255, 0, 0))
            final_score_text = font.render(f"Final Score: {int(distance_covered/10)}", True, (255, 255, 255))
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - game_over_text.get_height() // 2))
            screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - final_score_text.get_height() // 2 + 50))

        fps = int(clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
        screen.blit(fps_text, (15, 15))

        pygame.display.update()
        clock.tick()

    pygame.quit()

# Main loop
if __name__ == "__main__":
    while True:
        menu_selection = main_menu()
        if menu_selection == "Start Game":
            game_loop()
        elif menu_selection == "Exit":
            break
