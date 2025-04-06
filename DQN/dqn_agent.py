import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import csv
from actions import Action
import matplotlib.pyplot as plt
from collections import deque
import random

class DQNAgent:
    def __init__(self, state_size, action_size, learning_rate=0.001, gamma=0.99, replay_buffer_size=10000):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = 1.0
        self.epsilon_decay = 0.999
        self.epsilon_min = 0.01
        self.replay_buffer = deque(maxlen=replay_buffer_size)
        self.model = self._build_model()
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=1e-4)

    def _build_model(self):
        return nn.Sequential(
            nn.Linear(self.state_size, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, self.action_size)
        )

    def add_to_replay_buffer(self, state, action, next_state, reward, terminated):
        self.replay_buffer.append((state, action, next_state, reward, terminated))

    def sample_from_replay_buffer(self, batch_size):
        return random.sample(self.replay_buffer, min(len(self.replay_buffer), batch_size))

    def save_replay_buffer(self, file_path):
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Current_State", "Action", "New_State", "Reward", "Terminated"])
            for state, action, next_state, reward, terminated in self.replay_buffer:
                writer.writerow([state, action, next_state, reward, terminated])

    def load_replay_buffer(self, file_path):
        if not os.path.exists(file_path):
            return
        with open(file_path, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                state = eval(row["Current_State"])
                action = int(row["Action"])
                next_state = eval(row["New_State"])
                reward = float(row["Reward"])
                terminated = row["Terminated"] == "True"
                self.add_to_replay_buffer(state, action, next_state, reward, terminated)

    def normalize_state(self, state, max_distance=200):
        return [min(dist / max_distance, 1.0) for dist in state]

    def train(self, replay_buffer_file=None, batch_size=32, epochs=100):
        if replay_buffer_file:
            self.load_replay_buffer(replay_buffer_file)
        losses = []
        for epoch in range(epochs):
            for _ in range(len(self.replay_buffer) // batch_size):
                batch = self.sample_from_replay_buffer(batch_size)
                batch_states, batch_actions, batch_next_states, batch_rewards, batch_terminated = zip(*batch)
                batch_states = [self.normalize_state(state) for state in batch_states]
                batch_next_states = [self.normalize_state(state) for state in batch_next_states]
                batch_states = torch.tensor(batch_states, dtype=torch.float32)
                batch_actions = torch.tensor(batch_actions, dtype=torch.long)
                batch_next_states = torch.tensor(batch_next_states, dtype=torch.float32)
                batch_rewards = torch.tensor(batch_rewards, dtype=torch.float32)
                batch_terminated = torch.tensor(batch_terminated, dtype=torch.float32)
                q_values = self.model(batch_states)
                q_next_values = self.model(batch_next_states).detach()
                target_q_values = q_values.clone()
                for j in range(len(batch_states)):
                    action = batch_actions[j]
                    if batch_terminated[j]:
                        target_q_values[j, action] = batch_rewards[j]
                    else:
                        target_q_values[j, action] = batch_rewards[j] + self.gamma * torch.max(q_next_values[j])
                loss = self.criterion(q_values, target_q_values)
                losses.append(loss.item())
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
        plt.plot(losses)
        plt.title("Training Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.show()

    def get_action_from_model(self, state):
        normalized_state = self.normalize_state(state)
        state_tensor = torch.tensor(normalized_state, dtype=torch.float32).unsqueeze(0)
        q_values = self.model(state_tensor)
        action_index = torch.argmax(q_values).item()
        return list(Action)[action_index]

    def save_model(self, file_path):
        torch.save(self.model.state_dict(), file_path)

    def load_model(self, file_path):
        self.model.load_state_dict(torch.load(file_path))
        self.model.eval()
