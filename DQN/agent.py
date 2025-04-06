import math
import random
import sys
import os

import neat
import pygame

# Constants
WIDTH = 800
HEIGHT = 600

CAR_SIZE_X = 32
CAR_SIZE_Y = 32

BORDER_COLOR = (0,170,0) # Color To Crash on Hit

current_generation = 0 # Generation counter

class Car:

    def __init__(self, startx, starty):
        # Load Car Sprite and Rotate
        self.sprite = pygame.image.load('images/racing-car.png').convert_alpha() 
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite 

        # self.position = [690, 740] # Starting Position
        self.position = [startx, starty]  
        self.angle = 0
        self.speed = 0

        self.speed_set = False # Flag For Default Speed Later on

        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2] # Calculate Center

        self.radars = [] # List For Sensors / Radars
        self.drawing_radars = [] # Radars To Be Drawn

        self.alive = True # Boolean To Check If Car is Crashed

        self.distance = 0 # Distance Driven
        self.time = 0 # Time Passed

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position) # Draw Sprite
        self.draw_radar(screen) #OPTIONAL FOR SENSORS

    def draw_radar(self, screen):
        # Optionally Draw All Sensors / Radars

        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (255, 255, 255), self.center, position, 1)
            pygame.draw.circle(screen, (255, 255, 255), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            # If Any Corner Touches Border Color -> Crash
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def check_radar(self, degree, game_map):
        length = 1
        max_length = 150  # Max radar length

        while length < max_length:
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

            try:
                # If we hit the track boundary, stop
                if game_map.get_at((x, y)) == BORDER_COLOR:
                    break  
            except IndexError:
                # If we go out of bounds, use frame distance instead
                break  

            length += 1  

        # Calculate distance to the track boundary (if detected)
        track_dist = int(math.sqrt((x - self.center[0]) ** 2 + (y - self.center[1]) ** 2))

        # If an IndexError happened, calculate the frame boundary distance
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            frame_x = max(0, min(WIDTH - 1, x))  # Ensure within width
            frame_y = max(0, min(HEIGHT - 1, y))  # Ensure within height
            frame_dist = int(math.sqrt((frame_x - self.center[0]) ** 2 + (frame_y - self.center[1]) ** 2))
            dist = frame_dist  # Use frame distance if out of bounds
        else:
            dist = track_dist  # Use track distance otherwise

        self.radars.append([(x, y), dist])

    def update(self, game_map):
        # Set The Speed To 20 For The First Time
        # Only When Having 4 Output Nodes With Speed Up and Down
        if not self.speed_set:
            self.speed = 5
            self.speed_set = True

        # Get Rotated Sprite And Move Into The Right X-Direction
        # Don't Let The Car Go Closer Than 20px To The Edge
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Increase Distance and Time
        self.distance += self.speed
        self.time += 1
        
        # Same For Y-Position
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        # Calculate New Center
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Calculate Four Corners
        # Length Is Half The Side
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Check Collisions And Clear Radars
        self.check_collision(game_map)
        self.radars.clear()

        # From -90 To 120 With Step-Size 45 Check Radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self):
        # Get Distances To Border
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_alive(self):
        # Basic Alive Function
        return self.alive

    def get_reward(self):
        # Calculate Reward (Maybe Change?)
        # return self.distance / 50.0
        return self.distance / (CAR_SIZE_X / 2)

    def rotate_center(self, image, angle):
        # Rotate The Rectangle
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image


def run_simulation(genomes, config):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    global current_generation   
    current_generation += 1

    game_map = pygame.image.load('map.png').convert()
    #game_map = pygame.transform.scale(game_map, (WIDTH, HEIGHT))
    screen.blit(game_map, (0, 0))  
    pygame.display.flip()
    startx=0; starty=0
    done=False
    for i in range(800):
        for j in range(600):
            color=screen.get_at((i,j))
            if color.r==255 and color.g==0 and color.b==255:
                screen.set_at((i,j), (100,100,100))
                done=True
                startx=i; starty=j
                break
        if done:
            break
    #print(startx, starty)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    max_score = 0  # Track highest score
    max_iterations = 50  # Limit to 50 iterations
    final_message = ""

    for i, (genome_id, genome) in enumerate(genomes):  
        if i >= max_iterations or max_score >= 500:  # Stop if 50 iterations or max score 500
            break  

        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = 0  
        car = Car(startx, starty)

        current_score = 0  
        counter = 0

        while car.is_alive():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)

            # Get action from the neural network
            output = net.activate(car.get_data())
            choice = output.index(max(output))

            if choice == 0:
                car.angle += 2
            elif choice == 1:
                car.angle -= 2
            elif choice == 2:
                if car.speed - 0.5 >= 10:
                    car.speed -= 0.5
            else:
                car.speed += 0.5  

            # Update car and fitness
            car.update(game_map)
            genome.fitness += car.get_reward()
            current_score = car.distance/10

            # Update max score
            max_score = max(max_score, current_score)

            if max_score >= 500:
                break

            counter += 1
            if counter >= 30 * 40:  
                break

            # Draw everything
            screen.blit(game_map, (0, 0))
            car.draw(screen)

            # UI Text (White Color)
            iteration_text = font.render(f"Iteration: {i + 1}", True, (255, 255, 255))
            screen.blit(iteration_text, (10, 10))

            status_text = font.render("Status: Alive", True, (255, 255, 255))
            screen.blit(status_text, (10, 40))

            score_text = font.render(f"Score: {int(current_score)}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH - 150, 10))

            max_score_text = font.render(f"Max Score: {int(max_score)}", True, (255, 255, 255))
            screen.blit(max_score_text, (WIDTH - 150, 40))

            pygame.display.flip()
            clock.tick(60)  

        # Show death status
        screen.blit(game_map, (0, 0))  
        iteration_text = font.render(f"Iteration: {i + 1}", True, (255, 255, 255))
        screen.blit(iteration_text, (10, 10))

        status_text = font.render("Status: Dead", True, (255, 255, 255))
        screen.blit(status_text, (10, 40))

        score_text = font.render(f"Score: {int(current_score)}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH - 150, 10))

        max_score_text = font.render(f"Max Score: {int(max_score)}", True, (255, 255, 255))
        screen.blit(max_score_text, (WIDTH - 150, 40))

        pygame.display.flip()
        pygame.time.delay(500)  

    # Determine the final message
    if max_score >= 500:
        final_message = "Agent successfully completed 500 score"
    else:
        final_message = f"Agent could achieve {int(max_score)} score"

    # Final Screen - Show Max Score After 50 Iterations OR if max score 500 is reached
    screen.fill((0, 150, 0))  # Greenish background  
    final_text = font.render(final_message, True, (255, 255, 255))
    screen.blit(final_text, (WIDTH // 2 - 150, HEIGHT // 2))

    pygame.display.flip()
    pygame.time.delay(3000)  # Show result for 3 seconds before quitting

if __name__ == "__main__":
    # Load Config
    config_path = "ReinforcementLearning_Car_Game/config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create Population And Add Reporters
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # Run the simulation
    population.run(run_simulation, 25)

