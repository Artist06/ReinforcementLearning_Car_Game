import random
import numpy as np
from collections import deque
import csv
from datetime import datetime
from actions import Action  # Import the Action enum

class ReplayBuffer:
    def __init__(self, max_size, file_path_prefix="replay_buffer"):
        """
        Initialize the replay buffer.
        :param max_size: Maximum number of experiences to store in the buffer.
        :param file_path_prefix: Prefix for the CSV file where experiences will be saved.
        """
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size

        # Generate a unique file name using a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = f"{file_path_prefix}_{timestamp}.csv"

        # Initialize the CSV file with headers
        with open(self.file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Current_State", "Action", "New_State", "Reward", "Terminated"])

    def add(self, state, action, next_state, reward, done):
        """
        Add a new experience to the buffer with noise and imperfections.
        :param state: The current state of the environment.
        :param action: The action taken by the agent.
        :param next_state: The resulting state after taking the action.
        :param reward: The reward received for the action.
        :param done: Whether the episode terminated after this action.
        """
        # Add sensor noise to stored states
        state_noise = np.random.normal(0, 0.02, len(state))
        next_state_noise = np.random.normal(0, 0.02, len(next_state))
        
        # Add reward uncertainty
        reward_noise = np.random.normal(0, 0.05)
        
        # Store experience with imperfections
        self.buffer.append((
            np.array(state) + state_noise,
            action,
            np.array(next_state) + next_state_noise,
            reward + reward_noise,
            done
        ))
        
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)

        # Write the experience to the CSV file
        with open(self.file_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([state, action, next_state, reward, done])

    def sample(self, batch_size):
        """
        Sample a batch of experiences from the buffer with occasional duplicates and noise.
        :param batch_size: Number of experiences to sample.
        :return: A list of sampled experiences with noise.
        """
        # Sample with occasional duplicates to simulate memory glitches
        if random.random() < 0.05:  # 5% chance
            indices = random.choices(range(len(self.buffer)), k=batch_size)
        else:
            indices = random.sample(range(len(self.buffer)), batch_size)
            
        # Add temporal noise to sampled experiences
        samples = [self.buffer[i] for i in indices]
        noisy_samples = []
        
        for state, action, next_state, reward, done in samples:
            # Add time-dependent noise
            temporal_factor = random.uniform(0.98, 1.02)
            noisy_samples.append((
                state * temporal_factor,
                action,
                next_state * temporal_factor,
                reward,
                done
            ))
            
        return noisy_samples

    def size(self):
        """
        Get the current size of the buffer.
        :return: Number of experiences in the buffer.
        """
        return len(self.buffer)

def calculate_reward(ray_distances, is_within_track, distance_covered, speed, angle):
    reward = 0.0
    
    # Base track adherence
    if not is_within_track:
        return -100.0  # Severe penalty for going off track
    
    # Speed rewards/penalties
    if speed > 0:
        reward += speed * 3.0  # Reward forward motion
    else:
        reward -= abs(speed) * 5.0  # Heavy penalty for backward motion
    
    # Center tracking reward
    left_dist = ray_distances[0]
    right_dist = ray_distances[-1]
    center_diff = abs(left_dist - right_dist)
    
    # Exponential penalty for being off-center
    center_penalty = (center_diff / 50.0) ** 2
    reward -= center_penalty * 2.0
    
    # Bonus for perfect centering
    if center_diff < 10:
        reward += 2.0
    
    # Progress reward
    reward += distance_covered * 0.1
    
    # Smooth driving bonus
    if len(ray_distances) >= 3:
        smoothness = sum(abs(ray_distances[i] - ray_distances[i-1]) for i in range(1, len(ray_distances)))
        reward -= (smoothness / len(ray_distances)) * 0.01
    
    # Penalty for sharp angles
    angle_penalty = abs(angle) * 0.5  # Increase penalty factor for larger angles
    reward -= angle_penalty
    
    return reward