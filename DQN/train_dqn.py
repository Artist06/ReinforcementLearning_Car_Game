import os
import subprocess
import sys
import csv

# Ensure PyTorch is installed
try:
    import torch
except ImportError:
    print("PyTorch is not installed. Installing PyTorch...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision"])
    import torch  # Retry importing PyTorch after installation

from dqn_agent import DQNAgent
from actions import Action

# Extend the DQNAgent class to include replay buffer loading functionality
class ExtendedDQNAgent(DQNAgent):
    def load_replay_buffer(self, file_path):
        """
        Load experiences from a CSV file into the replay buffer.
        :param file_path: Path to the replay buffer CSV file.
        """
        if not os.path.exists(file_path):
            print(f"Replay buffer file '{file_path}' not found. Starting with an empty buffer.")
            return

        with open(file_path, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                state = eval(row["Current_State"])
                # Convert action name to its corresponding index
                action = self._action_to_index(row["Action"])
                next_state = eval(row["New_State"])
                reward = float(row["Reward"])
                terminated = row["Terminated"] == "True"
                self.add_to_replay_buffer(state, action, next_state, reward, terminated)
        print(f"Replay buffer loaded from {file_path}")

    def _action_to_index(self, action_name):
        """
        Convert an action name to its corresponding index.
        :param action_name: Name of the action (e.g., "UP", "IDLE").
        :return: Index of the action.
        """
        return list(Action).index(Action[action_name])

# Initialize the extended DQN agent
state_size = 8  # Number of ray distances
action_size = len(Action)  # Number of possible actions
agent = ExtendedDQNAgent(state_size, action_size)

# Path to the merged and balanced replay buffer file
replay_buffer_file = "merged_replay_buffer.csv"

# Check if the replay buffer file exists
if not os.path.exists(replay_buffer_file):
    print(f"Replay buffer file '{replay_buffer_file}' not found. Please generate it first.")
    sys.exit(1)

# Train the agent using the merged and balanced replay buffer file
print(f"Loading replay buffer from {replay_buffer_file}...")
agent.load_replay_buffer(replay_buffer_file)
print(f"Training with {replay_buffer_file}...")
agent.train(replay_buffer_file, batch_size=32, epochs=100)

# Save the trained model
model_path = "dqn_model.pth"
agent.save_model(model_path)
print(f"Model saved to {model_path}")