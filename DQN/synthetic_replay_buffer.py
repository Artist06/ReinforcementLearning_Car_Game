import numpy as np
import random
from collections import deque
import csv
from datetime import datetime
from actions import Action  # Import the Action enum

class SyntheticReplayBufferGenerator:
    def __init__(self, max_size=10000, file_path_prefix="synthetic_replay_buffer"):
        """
        Initialize the synthetic replay buffer generator.
        :param max_size: Maximum number of experiences to store in the buffer.
        :param file_path_prefix: Prefix for the CSV file where experiences will be saved.
        """
        self.buffer = deque(maxlen=max_size)
        
        # Generate a unique file name using a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = f"{file_path_prefix}_{timestamp}.csv"
        
        # Initialize the CSV file with headers
        with open(self.file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Current_State", "Action", "New_State", "Reward", "Terminated"])
    
    def generate_random_ray_dist(self, min_dist=10, max_dist=200):
        """
        Generate a random ray distance array simulating the ray cast results.
        :param min_dist: Minimum distance value
        :param max_dist: Maximum distance value
        :return: List of 8 ray distances
        """
        return [random.uniform(min_dist, max_dist) for _ in range(8)]
    
    def generate_sequential_state(self, previous_state=None, action=None):
        """
        Generate a sequential state based on previous state and action.
        This creates more realistic transitions than purely random states.
        
        :param previous_state: The previous ray distances
        :param action: The action taken
        :return: A new state that would reasonably follow from the previous state and action
        """
        if previous_state is None:
            # Generate a completely random initial state
            return self.generate_random_ray_dist()
        
        # Start with the previous state
        new_state = previous_state.copy()
        
        # Modify the state based on the action
        if action == Action.FORWARD:
            # Moving forward might slightly change distances
            new_state = [min(max(dist + random.uniform(-10, 15), 10), 200) for dist in new_state]
        
        elif action == Action.LEFT:
            # Turning left would generally increase distances on the right and decrease on the left
            for i in range(len(new_state)):
                if i < 4:  # Left side rays
                    new_state[i] = max(new_state[i] - random.uniform(5, 20), 10)
                else:  # Right side rays
                    new_state[i] = min(new_state[i] + random.uniform(5, 20), 200)
        
        elif action == Action.RIGHT:
            # Turning right would generally increase distances on the left and decrease on the right
            for i in range(len(new_state)):
                if i < 4:  # Left side rays
                    new_state[i] = min(new_state[i] + random.uniform(5, 20), 200)
                else:  # Right side rays
                    new_state[i] = max(new_state[i] - random.uniform(5, 20), 10)
        
        elif action == Action.BRAKE:
            # Braking might not change distances much
            new_state = [min(max(dist + random.uniform(-5, 5), 10), 200) for dist in new_state]
        
        elif action == Action.IDLE:
            # Idling would cause minimal changes
            new_state = [min(max(dist + random.uniform(-3, 3), 10), 200) for dist in new_state]
        
        # Add some randomness to create variety
        new_state = [min(max(dist + random.uniform(-3, 3), 10), 200) for dist in new_state]
        
        return new_state
    
    def calculate_synthetic_reward(self, state, action, new_state, terminated=False):
        """
        Calculate a synthetic reward based on the state, action, and new state.
        
        :param state: The current state
        :param action: The action taken
        :param new_state: The resulting state
        :param terminated: Whether the episode terminated
        :return: A reward value
        """
        # Base reward
        reward = 0
        
        # Check if any ray is too close (potential collision)
        min_dist = min(new_state)
        
        # Termination should result in a large negative reward
        if terminated:
            return -500
        
        # Being too close to an obstacle is bad
        if min_dist < 30:
            reward -= 50 * (30 - min_dist) / 30
        
        # Reward for having open space ahead
        forward_space = sum(new_state[2:6]) / 4  # Middle rays
        reward += forward_space / 20
        
        # Penalize idle actions
        if action == Action.IDLE:
            reward -= 10
            
        # Reward forward movement
        if action == Action.FORWARD and min_dist > 30:
            reward += 15
            
        # Penalize unnecessary braking
        if action == Action.BRAKE and min_dist > 50:
            reward -= 5
            
        # Reward appropriate turning when obstacles are closer on one side
        left_side = sum(new_state[:4])
        right_side = sum(new_state[4:])
        
        if left_side < right_side and action == Action.RIGHT:
            reward += 10
        elif right_side < left_side and action == Action.LEFT:
            reward += 10
            
        return reward
    
    def should_terminate(self, state):
        """
        Determine if the state should lead to termination.
        
        :param state: The current state
        :return: Boolean indicating termination
        """
        # Terminate if any ray distance is extremely close
        min_dist = min(state)
        if min_dist < 15:
            return random.random() < 0.8  # 80% chance of termination when very close
        elif min_dist < 30:
            return random.random() < 0.2  # 20% chance of termination when moderately close
        return False
    
    def generate_experiences(self, num_experiences, episode_length=100):
        """
        Generate a specified number of synthetic experiences.
        
        :param num_experiences: Total number of experiences to generate
        :param episode_length: Maximum length of each episode before reset
        """
        current_state = self.generate_random_ray_dist()
        episode_step = 0
        
        # Get number of actions in the Action enum
        num_actions = len(list(Action))
        
        for _ in range(num_experiences):
            # Select an action (with some intelligence to create better training data)
            min_dist = min(current_state)
            left_side = sum(current_state[:4])
            right_side = sum(current_state[4:])
            
            # Create action weights with proper length matching the Action enum
            action_weights = [0.0] * num_actions
            
            # Biased action selection based on the current state
            if min_dist < 30:
                # When close to obstacles, favor turning away or braking
                if left_side < right_side:
                    # Set weights for each action
                    if Action.FORWARD.value < num_actions:
                        action_weights[Action.FORWARD.value] = 0.1
                    if Action.LEFT.value < num_actions:
                        action_weights[Action.LEFT.value] = 0.1
                    if Action.RIGHT.value < num_actions:
                        action_weights[Action.RIGHT.value] = 0.6
                    if Action.BRAKE.value < num_actions:
                        action_weights[Action.BRAKE.value] = 0.2
                    if Action.IDLE.value < num_actions:
                        action_weights[Action.IDLE.value] = 0.0
                else:
                    # Set weights for each action
                    if Action.FORWARD.value < num_actions:
                        action_weights[Action.FORWARD.value] = 0.1
                    if Action.LEFT.value < num_actions:
                        action_weights[Action.LEFT.value] = 0.6
                    if Action.RIGHT.value < num_actions:
                        action_weights[Action.RIGHT.value] = 0.1
                    if Action.BRAKE.value < num_actions:
                        action_weights[Action.BRAKE.value] = 0.2
                    if Action.IDLE.value < num_actions:
                        action_weights[Action.IDLE.value] = 0.0
            else:
                # When path is clear, favor moving forward
                if Action.FORWARD.value < num_actions:
                    action_weights[Action.FORWARD.value] = 0.6
                if Action.LEFT.value < num_actions:
                    action_weights[Action.LEFT.value] = 0.15
                if Action.RIGHT.value < num_actions:
                    action_weights[Action.RIGHT.value] = 0.15
                if Action.BRAKE.value < num_actions:
                    action_weights[Action.BRAKE.value] = 0.05
                if Action.IDLE.value < num_actions:
                    action_weights[Action.IDLE.value] = 0.05
            
            # Normalize weights to ensure they sum to 1.0
            sum_weights = sum(action_weights)
            if sum_weights > 0:
                action_weights = [w / sum_weights for w in action_weights]
            else:
                # If all weights are 0, use uniform distribution
                action_weights = [1.0 / num_actions] * num_actions
            
            # Select an action based on the weights
            action_index = np.random.choice(num_actions, p=action_weights)
            action = list(Action)[action_index]
            
            # Generate the next state based on the current state and action
            new_state = self.generate_sequential_state(current_state, action)
            
            # Determine if this state should terminate
            terminated = self.should_terminate(new_state) or episode_step >= episode_length
            
            # Calculate a reward
            reward = self.calculate_synthetic_reward(current_state, action, new_state, terminated)
            
            # Add the experience to the buffer
            self.add(current_state, action, new_state, reward, terminated)
            
            # Update for the next iteration
            if terminated:
                current_state = self.generate_random_ray_dist()  # Reset state if terminated
                episode_step = 0
            else:
                current_state = new_state
                episode_step += 1
    
    def add(self, current_state, action, new_state, reward, terminated):
        """
        Add a new experience to the buffer and write it to the CSV file.
        
        :param current_state: The current state of the environment.
        :param action: The action taken by the agent (Action enum).
        :param new_state: The resulting state after taking the action.
        :param reward: The reward received for the action.
        :param terminated: Whether the episode terminated after this action.
        """
        # Add the experience to the buffer
        experience = (current_state, action, new_state, reward, terminated)
        self.buffer.append(experience)
        
        # Write the experience to the CSV file
        with open(self.file_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([current_state, action.name, new_state, reward, terminated])  # Save action as its name
    
    def get_buffer(self):
        """
        Get the generated replay buffer.
        
        :return: The replay buffer as a deque object
        """
        return self.buffer
    
    def load_to_agent(self, agent):
        """
        Load the generated experiences directly into a DQN agent.
        
        :param agent: The DQNAgent instance to load experiences into
        """
        for state, action, new_state, reward, terminated in self.buffer:
            action_index = list(Action).index(action)
            agent.add_to_replay_buffer(state, action_index, new_state, reward, terminated)
        
        print(f"Loaded {len(self.buffer)} experiences into the agent's replay buffer.")


def main():
    # Example usage
    buffer_size = 10000  # Number of experiences to generate
    generator = SyntheticReplayBufferGenerator(max_size=buffer_size)
    generator.generate_experiences(buffer_size)
    print(f"Generated {buffer_size} synthetic experiences and saved to {generator.file_path}")
    
    # If you want to load these experiences into your DQN agent:
    # from dqn_agent import DQNAgent
    # agent = DQNAgent(state_size=8, action_size=len(Action))
    # generator.load_to_agent(agent)
    

if __name__ == "__main__":
    main()