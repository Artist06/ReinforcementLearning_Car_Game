import torch
import numpy as np
from dqn_agent import DQNAgent
from actions import Action

# Initialize the DQN agent
state_size = 8  # Number of ray distances
action_size = len(Action)  # Number of possible actions
agent = DQNAgent(state_size, action_size)

# Load the trained model
model_path = "dqn_model.pth"
agent.load_model(model_path)

# Example function to use the model for decision-making
def get_action_from_model(state):
    """
    Use the trained DQN model to predict the best action for a given state.
    :param state: The current state of the environment (list of ray distances).
    :return: The action chosen by the model.
    """
    state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
    q_values = agent.model(state_tensor)  # Predict Q-values
    action_index = torch.argmax(q_values).item()  # Get the index of the action with the highest Q-value
    return list(Action)[action_index]  # Convert index to Action enum

# Example usage
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ([150, 150, 150, 150, 150, 150, 150, 150], "UP"),
        ([50, 150, 200, 250, 300, 200, 150, 50], "RIGHT"),
        ([300, 250, 200, 150, 100, 50, 50, 50], "LEFT"),
        ([50, 50, 50, 50, 50, 50, 50, 50], "IDLE"),
        ([300, 300, 300, 300, 300, 300, 300, 300], "UP"),
        ([150, 100, 50, 50, 50, 100, 150, 200], "UP"),
        ([200, 200, 200, 200, 50, 50, 50, 50], "LEFT"),
        ([50, 50, 50, 50, 200, 200, 200, 200], "RIGHT"),
    ]

    for i, (state, expected_action) in enumerate(test_cases, 1):
        action = get_action_from_model(state)
        print(f"Test Case {i}:")
        print(f"State: {state}")
        print(f"Predicted Action: {action.name}")
        print(f"Expected Action: {expected_action}")
        print("-" * 50)