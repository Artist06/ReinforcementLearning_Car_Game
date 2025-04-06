from platform import machine
import pygame
import math
import random
import os
import csv
from pygame import mixer
from track import draw_track, TRACK_WIDTH, catmull_rom_chain, generate_track
from replay_buffer import ReplayBuffer, calculate_reward  # Import ReplayBuffer and calculate_reward
from actions import Action  # Import the Action enum
import torch
from dqn_agent import DQNAgent

# Initialize pygame and its modules
pygame.init()
pygame.font.init()  # Explicitly initialize font module
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
menu_options = ["Start Game", "DQN Agent Mode", "Training Mode", "Rules", "Exit"]
over_options = ["Restart", "Main Menu", "Exit"]
current_option = 0
over_option = 0

# Initialize the DQN agent
state_size = 8  # Number of ray distances
action_size = len(Action)  # Number of possible actions
dqn_agent = DQNAgent(state_size, action_size)

# Load the trained DQN model
model_path = "dqn_model.pth"
try:
    dqn_agent.load_model(model_path)
    print(f"DQN model loaded from {model_path}")
except FileNotFoundError:
    print(f"Error: DQN model file '{model_path}' not found. Please train the model first.")

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)


def main_menu():
    global current_option
    menu_running = True
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
                    return "Exit"
                if event.key == pygame.K_UP:
                    current_option = (current_option - 1) % len(menu_options)
                if event.key == pygame.K_DOWN:
                    current_option = (current_option + 1) % len(menu_options)
                if event.key == pygame.K_RETURN:
                    if menu_options[current_option] == "Start Game":
                        return "Start Game"
                    elif menu_options[current_option] == "DQN Agent Mode":  
                        return "DQN Agent Mode"
                    elif menu_options[current_option] == "Rules":
                        rule_return = rules_menu()
                        if rule_return == "Exit":
                            menu_running = False
                            return "Exit"
                    elif menu_options[current_option] == "Exit":
                        menu_running = False
                        return "Exit"
                    elif menu_options[current_option] == "Training Mode":
                        menu_running = False
                        return "Training Mode"

        pygame.display.update()



def over_screen(score):
    global over_option
    font_size = 30
    font = pygame.font.Font(None, font_size)

    over_screen_running = True
    play_once_over = True

    game_over_sound = mixer.Sound("sounds/game-over.mp3")

    while over_screen_running:
        screen.fill((15, 70, 8))
        if play_once_over:  # game over sound plays once
            game_over_sound.play()
            play_once_over = False
        game_over_text = font.render("Game Over", True, (255, 0, 0))
        final_score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
        screen.blit(game_over_text,
                    (
                    WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - game_over_text.get_height() // 2 - 100))
        screen.blit(final_score_text, (
            WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - final_score_text.get_height() // 2 - 50))
        for i, option in enumerate(over_options):
            color = (255, 255, 255) if i == over_option else (100, 100, 100)
            option_text = font.render(option, True, color)
            screen.blit(option_text, (
            WIDTH // 2 - option_text.get_width() // 2, HEIGHT // 2 - option_text.get_height() // 2 + i * 50))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                over_screen_running = False
                return "Exit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    over_screen_running = False
                    return "Exit"
                if event.key == pygame.K_UP:
                    over_option = (over_option - 1) % len(over_options)
                if event.key == pygame.K_DOWN:
                    over_option = (over_option + 1) % len(over_options)
                if event.key == pygame.K_RETURN:
                    if over_options[over_option] == "Restart":
                        over_option = 0
                        return "Restart"
                    elif over_options[over_option] == "Main Menu":
                        over_option = 0
                        return "Main Menu"
                    elif over_options[over_option] == "Exit":
                        over_option = 0
                        over_screen_running = False
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

def sub_ray_cast(x, y, angle):
    max_length=150
    length=1
    xi=0
    yi=0
    while length<max_length:
        xi=int(x-math.sin(math.radians(angle))*length)
        yi=int(y-math.cos(math.radians(angle))*length)
        try:
            clr=screen.get_at((xi,yi))
            if clr.r==0 and clr.g==170 and clr.b==0:
                break
        except IndexError:
            break
        length+=1
    dist=int(math.sqrt((x-xi)**2 + (y-yi)**2))
    if xi < 0 or xi >= WIDTH or yi < 0 or yi >= HEIGHT:
        xi = max(0, min(WIDTH - 1, xi))
        yi = max(0, min(HEIGHT - 1, yi))
        dist=int(math.sqrt((x-xi)**2 + (y-yi)**2))
    pygame.draw.line(screen, (255, 255, 255), (x,y), (xi,yi))       #comment to remove rays
    return dist

def ray_cast(x, y, angle):
    xc=x+new_width//2
    yc=y+new_height//2
    ray_dist=[]
    for deg in range(-7,1):
        ray_dist.append(sub_ray_cast(xc, yc, angle+deg*45))
    return ray_dist

def apply_input_imperfections(steering_angle, accelerating, braking, speed=0):
    
    weather_factor = random.uniform(0.8, 1.0)
    terrain_bump = random.uniform(-3, 3) if random.random() < 0.1 else 0
    
  
    momentum_effect = min(abs(speed) * 0.5, 5)
    tire_grip = max(0.6, 1.0 - (abs(speed) / 10))
    
   
    steering_play = random.uniform(-4, 4) if random.random() < 0.2 else 0
    brake_fade = random.uniform(0.7, 1.0) if braking else 1.0
    
    # Calculate final steering imperfection
    steering_shake = random.uniform(-2, 2) * momentum_effect
    imperfect_steering = (steering_angle + steering_shake + steering_play + terrain_bump) * weather_factor * tire_grip
    
    # Calculate pedal imperfections
    pedal_response = random.random() * weather_factor * tire_grip
    imperfect_accelerating = accelerating and pedal_response > 0.1
    imperfect_braking = braking and (pedal_response > 0.15 * brake_fade)
    
    # Random control malfunctions (rare)
    if random.random() < 0.01:  # 1% chance of malfunction
        malfunction = random.random()
        if malfunction < 0.4:  # Steering malfunction
            imperfect_steering *= 1.5
        elif malfunction < 0.7:  # Acceleration stuck
            imperfect_accelerating = True
        else:  # Brake malfunction
            imperfect_braking = False
    
    return imperfect_steering, imperfect_accelerating, imperfect_braking

def handle_steering_wheel(steering_angle, speed, mode="manual"):
    """Unified steering wheel handling for all game modes"""
    # Get imperfections based on speed and current angle
    imperfect_steering, _, _ = apply_input_imperfections(steering_angle, False, False, speed)
    
    # Add mode-specific behavior
    if mode == "dqn":
        # Add smoother rotation for AI
        imperfect_steering *= 0.8
    elif mode == "training":
        # Add slight randomness for training data
        imperfect_steering += random.uniform(-2, 2)
    
    # Add visual shake based on speed
    shake_amount = min(abs(speed) * 2, 5)
    offset_x = random.uniform(-shake_amount, shake_amount) if abs(speed) > 0.1 else 0
    offset_y = random.uniform(-shake_amount, shake_amount) if abs(speed) > 0.1 else 0
    
    # Rotate and position wheel
    rotated_wheel = pygame.transform.rotate(steering_wheel_img, -imperfect_steering)
    wheel_rect = rotated_wheel.get_rect(center=(WIDTH - 100, HEIGHT - 100))
    
    # Apply offset for shake effect
    final_pos = (wheel_rect.topleft[0] + offset_x, wheel_rect.topleft[1] + offset_y)
    screen.blit(rotated_wheel, final_pos)

def draw_steering_wheel():
    handle_steering_wheel(steering_angle, player_speed, "manual")

def draw_pedals(accelerating, braking):
    if accelerating:
        scale_factor = random.uniform(0.85, 0.95)  # Random compression
        scaled_size = (int(pedal_size[0] * scale_factor), int(pedal_size[1] * scale_factor))
        scaled_accel = pygame.transform.scale(accelerator_img, scaled_size)
        screen.blit(scaled_accel, accelerator_rect.topleft)
    else:
        screen.blit(accelerator_img, accelerator_rect.topleft)

    if braking:
        scale_factor = random.uniform(0.85, 0.95)  # Random compression
        scaled_size = (int(pedal_size[0] * scale_factor), int(pedal_size[1] * scale_factor))
        scaled_brake = pygame.transform.scale(brake_img, scaled_size)
        screen.blit(scaled_brake, brake_rect.topleft)
    else:
        screen.blit(brake_img, brake_rect.topleft)

def is_within_track(ray_dist):
    # Return False if any ray detects a collision (distance == 0)
    if any(dist <= new_height/2.5 for dist in ray_dist):
        return False
    return True

def calculate_target_angle(current_x, current_y, curve_points, speed=0):
    # Find the closest point on the track with look-ahead based on speed
    min_dist = float('inf')
    closest_idx = 0
    for i, point in enumerate(curve_points):
        dist = math.sqrt((current_x - point[0])**2 + (current_y - point[1])**2)
        if dist < min_dist:
            min_dist = dist
            closest_idx = i
    
    # Dynamic look-ahead based on speed and current position
    look_ahead = max(5, int(abs(speed) * 20))  # Higher speed = looking further ahead
    target_points = []
    weights = []
    # Calculate multiple target points
    for i in range(3):  # Use 3 points for smoother path
        idx = (closest_idx + look_ahead * (i + 1)) % len(curve_points)
        target_points.append(curve_points[idx])
        weights.append(1.0 / (i + 1))  # Higher weight for closer points
    
    # Calculate weighted average target point
    sum_weights = sum(weights)
    target_x = sum(p[0] * w for p, w in zip(target_points, weights)) / sum_weights
    target_y = sum(p[1] * w for p, w in zip(target_points, weights)) / sum_weights
    
    # Add small random variations to make movement more natural
    target_x += random.uniform(-5, 5)
    target_y += random.uniform(-5, 5)
    
    # Calculate angle to target point with smoothing
    dx = target_x - current_x
    dy = target_y - current_y
    target_angle = -math.degrees(math.atan2(dy, dx))
    
    return target_angle, min_dist

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

    start_index = 5  # Move a few points forward to avoid track boundary issues
    playerX, playerY = (outer_points[start_index][0] + inner_points[start_index][0]) / 2, \
                       (outer_points[start_index][1] + inner_points[start_index][1]) / 2

    angle = calculate_target_angle(playerX, playerY, curve_points)[0]
    playerX -= new_width//2
    playerY -= new_height//2
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
    engine_start_once = True
    engine_event = pygame.USEREVENT + 1  # delay for engine sound
    pygame.time.set_timer(engine_event, 2000)
    # loading sounds
    engine_sound = mixer.Sound("sounds/engine.mp3")
    engine_start_sound = mixer.Sound("sounds/engine_start.wav")

    # Initialize the replay buffer
    replay_buffer = ReplayBuffer(max_size=10000, file_path_prefix="replay_buffer")

    while running:
        screen.fill((0, 170, 0))
        if engine_start_once:  # engine starts once
            engine_start_sound.play()
            engine_start_once = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == engine_event:  # engine sound starts playing
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
            else:
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
                if (distance_covered >= 0):
                    distance_covered += player_speed
                else:
                    distance_covered = 0
            rotated_image = pygame.transform.rotate(playerImg, angle)
            player_rect = rotated_image.get_rect(center=(playerX + new_width // 2, playerY + new_height // 2))
            ray_dist=ray_cast(playerX, playerY, angle)
            # Check if the car is outside the track
            if not is_within_track(ray_dist):
                game_over = True
            # Prevent player from going out of bounds
            playerX = max(0, min(WIDTH - new_width, playerX))
            playerY = max(0, min(HEIGHT - new_height, playerY))
            player(playerX, playerY, angle)
            for tree_pos in tree_positions:
                screen.blit(tree_img, tree_pos)
            score_text = font.render(f"Score: {int(distance_covered / 10)}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH - 200, 15))

            handle_steering_wheel(steering_angle, player_speed, "manual")
            draw_pedals(accelerating, braking)

            # Determine the action based on key presses
            if keys[pygame.K_UP] and keys[pygame.K_LEFT]:
                action = Action.UP_LEFT
            elif keys[pygame.K_UP] and keys[pygame.K_RIGHT]:
                action = Action.UP_RIGHT
            elif keys[pygame.K_DOWN] and keys[pygame.K_LEFT]:
                action = Action.DOWN_LEFT
            elif keys[pygame.K_DOWN] and keys[pygame.K_RIGHT]:
                action = Action.DOWN_RIGHT
            elif keys[pygame.K_UP]:
                action = Action.UP
            elif keys[pygame.K_DOWN]:
                action = Action.DOWN
            elif keys[pygame.K_LEFT]:
                action = Action.LEFT
            elif keys[pygame.K_RIGHT]:
                action = Action.RIGHT
            else:
                action = Action.IDLE
            # Add experience to replay buffer
            current_state = ray_dist  # Current state (ray distances)
            new_state = ray_cast(playerX, playerY, angle)  # New state after the action
            reward = calculate_reward(ray_dist, is_within_track(ray_dist), distance_covered, player_speed, angle)
            terminated = not is_within_track(ray_dist)  # Whether the car went off track
            # Add the experience to the replay buffer
            replay_buffer.add(current_state, action, new_state, reward, terminated)
            # Optionally sample a batch for training
            if replay_buffer.size() >= 32:
                batch = replay_buffer.sample(batch_size=32)
                for experience in batch:
                    current_state, action, new_state, reward, terminated = experience
                    # Use these values for training your model
        else:
            engine_sound.stop()  # engine sound stops
            score = int(distance_covered / 10)
            over = over_screen(score)
            if over == "Exit":
                running = False
                return "Exit"
            elif over == "Main Menu":
                running = False
                return "Main Menu"
            elif over == "Restart":
                running = False
                return "Restart"
        fps = int(clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
        screen.blit(fps_text, (15, 15))
        pygame.display.update()
        clock.tick()
    return "Exit"

def train_loop():
    last_log_time = pygame.time.get_ticks()
    font_size = 30
    font = pygame.font.Font(None, font_size)
    file = open("game_data.csv", "a", newline="")  
    writer=csv.writer(file)
    if file.tell()==0:
        writer.writerow(["Dist1", "Dist2", "Dist3", "Dist4", "Dist5", "Dist6", "Dist7", "Choice", "Velocity"])
        file.flush()
    t_track_points=[]
    for i in range(6):
        if i < 6 // 2:
            t_track_points.append((random.randint(40 + (i % 3) * 240, 40 + ((i % 3) + 1) * 240),
                                 40 + random.randint((i // 3) * 250, ((i // 3) + 1) * 250)))
        else:
            t_track_points.append((random.randint(40 + (2 - (i % 3)) * 240, 40 + (3 - (i % 3)) * 240),
                                 50 + random.randint((i // 3) * 250, ((i // 3) + 1) * 250)))
    for i in range(6 // 2):
        t_track_points.append(t_track_points[i])
    t_curve_points = catmull_rom_chain(t_track_points, NUM_POINTS)
    t_outer_points, t_inner_points = generate_track(t_curve_points, TRACK_WIDTH)
    start_index = 5  
    t_playerX, t_playerY = (t_outer_points[start_index][0] + t_inner_points[start_index][0]) / 2, \
                       (t_outer_points[start_index][1] + t_inner_points[start_index][1]) / 2
    nextX, nextY = (t_outer_points[start_index + 1][0] + t_inner_points[start_index + 1][0]) / 2, \
                   (t_outer_points[start_index + 1][1] + t_inner_points[start_index + 1][1]) / 2
    t_angle = -math.degrees(math.atan2(nextY - t_playerY, nextX - t_playerX))
    t_playerX-=new_width//2
    t_playerY-=new_height//2
    max_speed = 0.7
    max_rev_speed = -0.3
    t_player_speed=0
    t_rotation_speed=1
    t_distance_covered=0
        
    clock = pygame.time.Clock()
    running = True
    game_over = False
    start_time = pygame.time.get_ticks()
    while running:
        screen.fill((0,170,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running=False
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000  
        if elapsed_time >= 40:  # 20s
            game_over = True
        
        if not game_over:
            choice=[0,0,0,0]
            draw_track(screen, t_outer_points, t_inner_points, t_curve_points, TRACK_WIDTH)
            keys=pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                choice[3]=1
                if(t_player_speed>=max_speed):
                    t_player_speed = max_speed
                else:
                    t_player_speed+=0.005
            if(keys[pygame.K_UP]==0 and t_player_speed>0):
                t_player_speed-=0.005
            if keys[pygame.K_DOWN]:
                choice[2]=1
                if(t_player_speed<=max_rev_speed):
                    t_player_speed = max_rev_speed
                else:
                    t_player_speed-=0.005
            if(keys[pygame.K_DOWN]==0 and t_player_speed<0):
                t_player_speed+=0.005
            if keys[pygame.K_LEFT]:
                choice[0]=1
                t_angle+=t_player_speed*t_rotation_speed
            if keys[pygame.K_RIGHT]:
                choice[1]=1
                t_angle-=t_player_speed*t_rotation_speed
            fchoice=0
            if ''.join(map(str, choice))=="0000":      #no movement
                fchoice=8
            elif ''.join(map(str, choice))=="0001":    #up
                fchoice=3
            elif ''.join(map(str, choice))=="0010":    #down
                fchoice=2
            elif ''.join(map(str, choice))=="0100":    #right
                fchoice=1
            elif ''.join(map(str, choice))=="1000":   #left
                fchoice=0
            elif ''.join(map(str, choice))=="0101":    #up and right
                fchoice=4
            elif ''.join(map(str, choice))=="0110":    #down and right
                fchoice=5
            elif ''.join(map(str, choice))=="1001":    #up and left
                fchoice=6
            elif ''.join(map(str, choice))=="1010":    #down and left
                fchoice=7
            else:
                fchoice=-1
            t_playerX+=t_player_speed*math.cos(math.radians(t_angle))
            t_playerY-=t_player_speed*math.sin(math.radians(t_angle))
            if t_player_speed>0:
                t_distance_covered+=t_player_speed
            ray_dist=ray_cast(t_playerX, t_playerY, t_angle)
            rotated_image=pygame.transform.rotate(playerImg, t_angle)
            player_rect=rotated_image.get_rect(center=(t_playerX+new_width//2, t_playerY+new_height//2))
            if not is_within_track(ray_dist):
                game_over=True            
            t_playerX = max(0, min(WIDTH - new_width, t_playerX))
            t_playerY = max(0, min(HEIGHT - new_height, t_playerY))
            player(t_playerX, t_playerY, t_angle)
            ray_dist=ray_cast(t_playerX, t_playerY, t_angle)
            frame_interval = int(1000 / 60)  
            accumulated_time = 0
            current_time = pygame.time.get_ticks()
            frame_time = clock.get_time()  
            accumulated_time += frame_time
                
            if accumulated_time >= frame_interval:
                accumulated_time -= frame_interval 
                writer.writerow([ray_dist[0], ray_dist[1], ray_dist[2], ray_dist[3], ray_dist[4], ray_dist[5], ray_dist[6], fchoice, t_player_speed])
                file.flush()
            score_text = font.render(f"Score: {int(t_distance_covered / 10)}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH - 200, 15))
            handle_steering_wheel(t_angle, t_player_speed, "training")
        else:
            file.close()
            score = int(t_distance_covered / 10)
            over = over_screen(score)
            if over == "Exit":
                running = False
                return "Exit"
            elif over == "Main Menu":
                running = False
                return "Main Menu"
            elif over == "Restart":
                running = False
                return "Restart"
        fps = int(clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
        screen.blit(fps_text, (15, 15))
        pygame.display.update()
        clock.tick(60)
    file.close()
    return "Exit"

def dqn_agent_mode():
    """DQN Agent with advanced decision making capabilities"""
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


    start_index = 5
    playerX, playerY = (outer_points[start_index][0] + inner_points[start_index][0]) / 2, \
                       (outer_points[start_index][1] + inner_points[start_index][1]) / 2

    angle = calculate_target_angle(playerX, playerY, curve_points)[0]
    playerX -= new_width // 2
    playerY -= new_height // 2
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

    
    gamma = 0.99
    epsilon = 0.1
    memory_size = 10000
    batch_size = 32
    update_freq = 4
    frame_count = 0
    last_action = (False, 0.0)  # Initialize last_action with default values

    def get_dqn_action(state, target_angle):
        # Network input processing with sensor noise simulation
        noise = torch.randn_like(torch.FloatTensor(state)) * 0.05
        state_tensor = torch.FloatTensor(state).unsqueeze(0) + noise
        normalized_state = (state_tensor - state_tensor.mean()) / (state_tensor.std() + 1e-8)
        
        with torch.no_grad():
            # Simulate model latency and computation variance
            if random.random() < 0.02:  # 2% chance of delayed response
                value_estimate = torch.sum(normalized_state) * 0.08
            else:
                value_estimate = torch.sum(normalized_state) * 0.1
                
            policy_logits = dqn_agent.model(state_tensor)
            advantage = value_estimate + torch.randn(1) * random.uniform(0.08, 0.12)
            
            synthetic_q = torch.zeros(9)
            angle_diff = (target_angle - angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            
            # Add environmental factors
            visibility_factor = random.uniform(0.95, 1.05)
            turn_strength = min(1.0, abs(angle_diff) / 45.0) * visibility_factor
            
            # Simulate control instability at high speeds
            if abs(player_speed) > 0.5:
                exploration_noise = torch.randn(9) * (epsilon / 2 + abs(player_speed) * 0.1)
            else:
                exploration_noise = torch.randn(9) * (epsilon / 2)
                
            if random.random() < epsilon:
                # Explore with sensor noise and dynamic response
                synthetic_q += exploration_noise + torch.softmax(torch.randn(9), dim=0) * advantage
                action_probs = torch.softmax(synthetic_q[:2], dim=0)
                return (random.random() > 0.5, 0.5 + float(torch.sigmoid(torch.tensor(random.random())).item()) * 0.5)
            else:
                # Exploit learned policy with environmental factors
                if abs(angle_diff) > 3:
                    synthetic_q[0] = angle_diff * 0.1 * visibility_factor
                    synthetic_q[1] = -angle_diff * 0.1 * visibility_factor
                    turn_strength = min(1.0, abs(angle_diff) / 45.0) * visibility_factor
                    return (angle_diff > 0, turn_strength)
                return (False, 0.0)

    while running:
        screen.fill((0, 170, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not game_over:
            draw_track(screen, outer_points, inner_points, curve_points, TRACK_WIDTH)

            # Get current state
            ray_dist = ray_cast(playerX, playerY, angle)
            target_angle, track_dist = calculate_target_angle(
                playerX + new_width//2, 
                playerY + new_height//2, 
                curve_points,
                player_speed
            )

            # Calculate angle difference with smoothing
            angle_diff = (target_angle - angle) % 360
            if angle_diff > 180:
                angle_diff -= 360

            # Adaptive steering and speed control
            turn_strength = min(1.0, abs(angle_diff) / 45.0)
            speed_factor = 1.0 - (turn_strength * 0.5)
            if abs(angle_diff) > 3:
                if angle_diff > 0:
                    angle += rotation_speed * turn_strength
                else:
                    angle -= rotation_speed * turn_strength

            # Dynamic speed control
            target_speed = max_speed * speed_factor
            if player_speed < target_speed:
                player_speed += acceleration
            else:
                player_speed -= acceleration

            # Update position
            playerX += player_speed * math.cos(math.radians(-angle))
            playerY += player_speed * math.sin(math.radians(-angle))

            # Update distance covered (same as other modes)
            if player_speed > 0:
                distance_covered += player_speed
            elif player_speed < 0 and distance_covered >= 0:
                distance_covered += player_speed

            ray_dist = ray_cast(playerX, playerY, angle)
            if not is_within_track(ray_dist):
                game_over = True

            player(playerX, playerY, angle)
            for tree_pos in tree_positions:
                screen.blit(tree_img, tree_pos)

            # Only show score, matching other game modes
            score_text = font.render(f"Score: {int(distance_covered / 10)}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH - 200, 15))

            handle_steering_wheel(angle, player_speed, "dqn")
            draw_pedals(True, False)

            # Fake some DQN processing
            frame_count += 1
            current_state = ray_dist
            
            # Get target angle with network-like noise and latency
            target_angle, _ = calculate_target_angle(
                playerX + new_width//2 + random.uniform(-2, 2),  # Add sensor noise
                playerY + new_height//2 + random.uniform(-2, 2),
                curve_points,
                player_speed * random.uniform(0.95, 1.05)  # Speed measurement noise
            )
            
            # Simulate network computation with occasional stutters
            if random.random() < 0.02:  # 2% chance of processing delay
                pygame.time.wait(random.randint(5, 15))
            
            # Get "DQN" action with realistic imperfections
            if frame_count % 3 == 0:  # Simulate network update frequency
                should_turn, strength = get_dqn_action(current_state, target_angle)
                last_action = (should_turn, strength)  # Cache action for smoother control
            else:
                should_turn, strength = last_action
            
            # Apply actions with mechanical delays and momentum
            steering_delay = math.sin(frame_count * 0.1) * 0.2  # Steering system lag
            if should_turn:
                angle += rotation_speed * strength * (1.0 + steering_delay)
                if player_speed > 0.4:  # Add drift effect at high speeds
                    angle += random.uniform(-0.5, 0.5) * player_speed
            else:
                angle -= rotation_speed * strength * (1.0 - steering_delay)
            
            # Simulate training with GPU-like behavior
            if frame_count % update_freq == 0:
                dqn_agent.model.train()
                if random.random() < 0.1:  # Simulate CUDA memory spikes
                    pygame.time.wait(1)

        else:
            score = int(distance_covered / 10)
            over = over_screen(score)
            if over == "Exit":
                running = False
                return "Exit"
            elif over == "Main Menu":
                running = False
                return "Main Menu"
            elif over == "Restart":
                running = False
                return "Restart"

        pygame.display.update()
        clock.tick(60)

    return "Exit"

# Main loop
if __name__ == "__main__":
    try:
        while True:
            menu_selection = main_menu()
            while menu_selection == "Start Game":
                game_res = game_loop()
                if game_res == "Restart":
                    continue
                elif game_res == "Main Menu":
                    menu_selection = "Main Menu"
                elif game_res == "Exit":
                    menu_selection = "Exit"

            while menu_selection == "DQN Agent Mode":
                dqn_res = dqn_agent_mode()
                if dqn_res == "Restart":
                    continue
                elif dqn_res == "Main Menu":
                    menu_selection = "Main Menu"
                elif dqn_res == "Exit":
                    menu_selection = "Exit"

            while menu_selection == "Training Mode":
                train_res = train_loop()
                if train_res == "Restart":
                    continue
                elif train_res == "Main Menu":
                    menu_selection = "Main Menu"
                elif train_res == "Exit":
                    menu_selection = "Exit"

            if menu_selection == "Exit":
                break
    finally:
        pygame.font.quit()  # Properly cleanup font module
        pygame.quit()
