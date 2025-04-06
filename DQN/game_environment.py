import pygame
import numpy as np
import math
import random
import os
from track import generate_track, draw_track, catmull_rom_chain
from config import *

class GameEnvironment:
    def __init__(self, headless=False):
        # Initialize pygame
        if not pygame.get_init():
            pygame.init()
            
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.headless = headless
        
        if not headless:
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
            pygame.display.set_caption("Track Invaders - AI Training")
        else:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.Surface((self.WIDTH, self.HEIGHT))
            
        # Load the player image
        self.playerImg = pygame.image.load('images/racing-car.png')
        self.new_width = 48
        self.new_height = int((self.new_width / self.playerImg.get_width()) * self.playerImg.get_height())
        self.playerImg = pygame.transform.scale(self.playerImg, (self.new_width, self.new_height))
        
        # Initialize track
        self.initialize_track()
        
        # Game state variables
        self.speed = 0.0
        self.score = 0
        self.distance_covered = 0
        self.steps_taken = 0
        self.current_checkpoint = 0
        
        # Reset environment
        self.reset()

    def generate_track_points(self):
        """Generate random track points"""
        track_points = []
        for i in range(6):
            if i < 6 // 2:
                track_points.append((
                    random.randint(40 + (i % 3) * 240, 40 + ((i % 3) + 1) * 240),
                    40 + random.randint((i // 3) * 250, ((i // 3) + 1) * 250)
                ))
            else:
                track_points.append((
                    random.randint(40 + (2 - (i % 3)) * 240, 40 + (3 - (i % 3)) * 240),
                    50 + random.randint((i // 3) * 250, ((i // 3) + 1) * 250)
                ))
        
        for i in range(6 // 2):
            track_points.append(track_points[i])
        return track_points

    def initialize_track(self):
        """Initialize track and create track image"""
        self.track_points = self.generate_track_points()
        self.curve_points = catmull_rom_chain(self.track_points, NUM_CURVE_POINTS)
        self.outer_points, self.inner_points = generate_track(self.curve_points, TRACK_WIDTH)
        
        # Create track image
        self.track_img = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.track_img.fill((0, 170, 0))  # Green background
        draw_track(self.track_img, self.outer_points, self.inner_points, self.curve_points, TRACK_WIDTH)

    def reset(self):
        """Reset the environment to initial state"""
        # Reset track if needed
        if not hasattr(self, 'track_points') or not self.track_points:
            self.initialize_track()
        
        # Start at the beginning of the track
        start_point = self.curve_points[0]
        self.playerX = start_point[0] - self.new_width//2
        self.playerY = start_point[1] - self.new_height//2
        
        # Calculate initial angle based on next track point
        next_point = self.curve_points[1]
        dx = next_point[0] - start_point[0]
        dy = next_point[1] - start_point[1]
        self.angle = math.degrees(math.atan2(-dy, dx))
        
        # Reset game state
        self.speed = 0.0
        self.score = 0
        self.distance_covered = 0
        self.steps_taken = 0
        self.current_checkpoint = 0
        
        # Draw initial state
        if not self.headless:
            self.screen.blit(self.track_img, (0, 0))
            self.render()
            pygame.display.flip()
        
        # Get initial state
        ray_distances = self.get_ray_distances()
        return np.array([
            *ray_distances,
            self.speed / 0.7,  # Normalized speed
            math.sin(math.radians(self.angle)),
            math.cos(math.radians(self.angle))
        ]).reshape(1, -1)

    def get_ray_distances(self):
        """Get distances to track boundaries using raycasting"""
        ray_distances = []
        center_x = self.playerX + self.new_width//2
        center_y = self.playerY + self.new_height//2
        
        # Cast rays at different angles
        num_rays = 8
        angles = np.linspace(-90, 90, num_rays)
        max_length = 150
        
        for ray_angle in angles:
            ray_angle_rad = math.radians(self.angle + ray_angle)
            min_dist = max_length
            
            # Cast ray
            ray_end_x = center_x + max_length * math.cos(ray_angle_rad)
            ray_end_y = center_y + max_length * math.sin(ray_angle_rad)
            
            # Check track boundaries
            for i in range(len(self.outer_points) - 1):
                # Check outer boundary
                outer_dist = self.ray_segment_intersection(
                    center_x, center_y, ray_end_x, ray_end_y,
                    self.outer_points[i][0], self.outer_points[i][1],
                    self.outer_points[i+1][0], self.outer_points[i+1][1]
                )
                if outer_dist is not None and outer_dist < min_dist:
                    min_dist = outer_dist
                
                # Check inner boundary
                inner_dist = self.ray_segment_intersection(
                    center_x, center_y, ray_end_x, ray_end_y,
                    self.inner_points[i][0], self.inner_points[i][1],
                    self.inner_points[i+1][0], self.inner_points[i+1][1]
                )
                if inner_dist is not None and inner_dist < min_dist:
                    min_dist = inner_dist
            
            ray_distances.append(min_dist / max_length)  # Normalize distances
            
            # Visualize rays in non-headless mode
            if not self.headless:
                end_x = center_x + min_dist * math.cos(ray_angle_rad)
                end_y = center_y + min_dist * math.sin(ray_angle_rad)
                pygame.draw.line(self.screen, (255, 0, 0), (center_x, center_y), (end_x, end_y), 1)
        
        return ray_distances

    def ray_segment_intersection(self, ray_x, ray_y, ray_end_x, ray_end_y,
                               seg_start_x, seg_start_y, seg_end_x, seg_end_y):
        """Calculate intersection between ray and line segment"""
        # Ray direction
        ray_dx = ray_end_x - ray_x
        ray_dy = ray_end_y - ray_y
        
        # Segment direction
        seg_dx = seg_end_x - seg_start_x
        seg_dy = seg_end_y - seg_start_y
        
        # Calculate denominator
        denom = ray_dx * seg_dy - ray_dy * seg_dx
        if abs(denom) < 1e-8:  # Parallel lines
            return None
        
        # Calculate intersection parameters
        t = ((seg_start_x - ray_x) * seg_dy - (seg_start_y - ray_y) * seg_dx) / denom
        u = ((ray_x - seg_start_x) * ray_dy - (ray_y - seg_start_y) * ray_dx) / -denom
        
        # Check if intersection is within segments
        if 0 <= t <= 1 and 0 <= u <= 1:
            return t * math.sqrt(ray_dx**2 + ray_dy**2)
        return None

    def step(self, action):
        """Take action and return new state, reward, done, info"""
        # Movement parameters
        acceleration = 0.005
        max_speed = 0.7
        friction = 0.005
        reverse_speed = -0.3
        rotation_speed = 0.8

        # Apply action
        is_accelerating = action == 2
        is_braking = action == 3
        is_turning_left = action == 0
        is_turning_right = action == 1

        # Update speed
        if is_accelerating:
            if self.speed < 0:
                self.speed += friction
            else:
                self.speed += acceleration
                if self.speed > max_speed:
                    self.speed = max_speed
        elif is_braking:
            if self.speed > 0:
                self.speed -= friction
            else:
                self.speed -= acceleration
                if self.speed < reverse_speed:
                    self.speed = reverse_speed
        else:
            if self.speed > 0:
                self.speed -= friction
            elif self.speed < 0:
                self.speed += friction
            if abs(self.speed) < friction:
                self.speed = 0

        # Update angle
        if self.speed != 0:
            direction = 1 if self.speed > 0 else -1
            if is_turning_left:
                self.angle += rotation_speed * direction
            if is_turning_right:
                self.angle -= rotation_speed * direction

        # Update position
        self.playerX += self.speed * math.cos(math.radians(-self.angle))
        self.playerY += self.speed * math.sin(math.radians(-self.angle))
        self.steps_taken += 1

        # Check if car is on track
        rotated_car = pygame.transform.rotate(self.playerImg, self.angle)
        car_rect = rotated_car.get_rect(center=(
            self.playerX + self.new_width//2,
            self.playerY + self.new_height//2
        ))
        done = not self.is_car_on_track(car_rect)

        # Update score and calculate reward
        old_score = self.score
        if self.speed > 0:
            self.distance_covered += self.speed
            self.score = int(self.distance_covered / 10)

        # Calculate reward
        reward = (self.score - old_score) * 10  # Reward for increasing score
        if done:
            reward = -50  # Penalty for going off track

        # Draw current state
        if not self.headless:
            self.render()

        # Get new state
        ray_distances = self.get_ray_distances()
        state = np.array([
            *ray_distances,
            self.speed / max_speed,  # Normalized speed
            math.sin(math.radians(self.angle)),
            math.cos(math.radians(self.angle))
        ])

        info = {
            'score': self.score,
            'distance': self.distance_covered,
            'speed': self.speed,
            'steps': self.steps_taken
        }

        return state.reshape(1, -1), reward, done, info

    def render(self):
        """Render the current state"""
        if not self.headless:
            # Draw track
            self.screen.blit(self.track_img, (0, 0))
            
            # Draw car
            rotated_car = pygame.transform.rotate(self.playerImg, self.angle)
            car_rect = rotated_car.get_rect(center=(
                self.playerX + self.new_width//2,
                self.playerY + self.new_height//2
            ))
            self.screen.blit(rotated_car, car_rect.topleft)
            
            # Update display
            pygame.display.flip()