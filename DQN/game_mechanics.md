# Game Mechanics

This document outlines the core mechanics of the reinforcement learning car game.

## Overview
The game involves a car navigating through a track using reinforcement learning. The car is trained to maximize its performance by learning from its environment and adjusting its actions accordingly.

## Key Mechanics
- **State Representation**: The car's state includes its position, velocity, and orientation, as well as distances to obstacles.
- **Actions**: The car can accelerate, decelerate, or turn left/right.
- **Rewards**: The car receives positive rewards for staying on track and reaching checkpoints, and negative rewards for collisions or going off-track.
- **Environment**: The track is procedurally generated with varying difficulty levels.

## Objective
The goal is to train the car to complete the track as efficiently as possible without collisions.

