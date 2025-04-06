# Track Invaders - Car Racing Game

## Overview

This Python code implements a car racing game using the Pygame library. The game features a main menu, agent mode, training mode, rules screen, and game over screen. Players control a car on a procedurally generated track, aiming to stay within the track boundaries.

## Features

* **Main Menu:** Provides options to start the game, enter agent mode, training mode, view rules, or exit.
* **Training Mode:** Saves game data (ray distances, chosen action, velocity) to a CSV file (`game_data.csv`) for machine learning purposes.
* **Rules Screen:** Explains the game controls and objective.
* **Game Over Screen:** Displays the final score and options to restart, return to the main menu, or exit.
* **Dynamic Obstacles:** Trees are randomly placed as obstacles.
* **Ray Casting:** Implemented for collision detection and potentially for AI agent input.
* **Steering Wheel and Pedal Indicators:** Visual representation of steering and acceleration/braking.

## Dependencies

* pygame
* math
* random
* os
* csv
* agent.py (if using agent mode)
* images folder (containing: racing.png, racing-car.png, steering-wheel.png, brake.png, accelerator.png, grass.png)
* sounds folder (containing: engine.mp3, engine_start.wav, game-over.mp3)

## Usage

1. Make sure you have all the dependencies installed (`pip install pygame`).
2. Place all the images and sounds in the appropriate folders.
3. Run the script `updated_main.py`.
4. Use the main menu to navigate and select game modes.

## Controls

* **Arrow Keys:**
  * `UP`: Accelerate
  * `DOWN`: Brake/Reverse
  * `LEFT`: Steer Left
  * `RIGHT`: Steer Right
* **ESC:** Exit to main menu (or quit during main menu).
* **ENTER:** Select menu option.
