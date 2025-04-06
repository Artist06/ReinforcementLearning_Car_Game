import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random

class RLNetwork(nn.Module):
    def __init__(self, input_size=7, hidden_size=128, output_size=6):
        super(RLNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )
    
    def forward(self, x):
        return self.network(x)

class RLAgent:
    def __init__(self, state_size=7, action_size=6):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95  # discount factor
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        self.model = RLNetwork(state_size, 128, action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if isinstance(state, list):
            state = torch.FloatTensor(state).unsqueeze(0)
        return self.model(state).argmax().item()

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            if isinstance(state, list):
                state = torch.FloatTensor(state).unsqueeze(0)
            if isinstance(next_state, list):
                next_state = torch.FloatTensor(next_state).unsqueeze(0)
                
            target = reward
            if not done:
                target = reward + self.gamma * torch.max(self.model(next_state)).item()
            
            target_f = self.model(state)
            target_f[0][action] = target
            
            self.optimizer.zero_grad()
            loss = self.criterion(self.model(state), target_f)
            loss.backward()
            self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save(self, path):
        torch.save(self.model.state_dict(), path)

    def load(self, path):
        self.model.load_state_dict(torch.load(path))
