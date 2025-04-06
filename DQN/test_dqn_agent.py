import os
import unittest
import torch
from dqn_agent import DQNAgent
from actions import Action

class TestDQNAgent(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment.
        Initialize a DQNAgent instance and create a temporary replay buffer file for testing.
        """
        self.state_size = 8  # Number of ray distances
        self.action_size = len(Action)  # Number of possible actions
        self.agent = DQNAgent(self.state_size, self.action_size)

        # Create a temporary replay buffer file
        self.replay_buffer_file = "test_replay_buffer.csv"
        with open(self.replay_buffer_file, "w") as file:
            file.write("Current_State,Action,New_State,Reward,Terminated\n")
            file.write("[100, 120, 80, 60, 50, 40, 30, 20],UP,[110, 130, 90, 70, 60, 50, 40, 30],10.0,False\n")
            file.write("[110, 130, 90, 70, 60, 50, 40, 30],DOWN,[100, 120, 80, 60, 50, 40, 30, 20],-5.0,True\n")

    def tearDown(self):
        """
        Clean up after tests.
        Remove the temporary replay buffer file.
        """
        if os.path.exists(self.replay_buffer_file):
            os.remove(self.replay_buffer_file)

    def test_model_initialization(self):
        """
        Test if the DQN model is initialized correctly.
        """
        self.assertIsNotNone(self.agent.model, "Model should be initialized.")
        self.assertEqual(len(list(self.agent.model.parameters())), 6, "Model should have 6 layers (weights and biases).")

    def test_training(self):
        """
        Test if the agent can train on the replay buffer file without errors.
        """
        try:
            self.agent.train(self.replay_buffer_file, batch_size=2, epochs=1)
        except Exception as e:
            self.fail(f"Training failed with exception: {e}")

    def test_save_and_load_model(self):
        """
        Test if the model can be saved and loaded correctly.
        """
        model_path = "test_dqn_model.pth"
        self.agent.save_model(model_path)

        # Ensure the model file is created
        self.assertTrue(os.path.exists(model_path), "Model file should be saved.")

        # Load the model and ensure no errors occur
        try:
            self.agent.load_model(model_path)
        except Exception as e:
            self.fail(f"Loading model failed with exception: {e}")

        # Clean up the saved model file
        if os.path.exists(model_path):
            os.remove(model_path)

    def test_action_to_index(self):
        """
        Test if the action-to-index conversion works correctly.
        """
        action_index = self.agent._action_to_index("UP")
        self.assertEqual(action_index, list(Action).index(Action.UP), "Action index should match the enum index.")

if __name__ == "__main__":
    unittest.main()