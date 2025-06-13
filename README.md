# Turn-Based Strategy Game

## Overview

This project is a 2D isometric turn-based strategy game built in Python using [Pygame](https://www.pygame.org/). Inspired by the Age of Empires games on the Nintendo DS, it offers a grid-based combat experience where players command units, construct buildings, and battle against AI-controlled enemies.

## Features

- **Classic Turn-Based Gameplay:**  
  Players and enemy AI take turns advancing their empire, by attacking other units, constructing buildings, and gathering resources. 
- **AI Opponents:**  
  Enemies use pathfinding and decision logic to seek out and attack player-controlled units and buildings.
- **Fog of War:**  
  Map visibility is limited by the vision range of your units, hiding enemy movements and adding tactical depth.
- **Resource Management:**  
  Players can use units like villagers to gather resources such as food, wood, and gold. They can also build and manage structures to increase your capabilities and population limits.
- **Custom UI Elements:**  
  Includes basic prototype UI such as translucent message boxes and pop-up notifications.
- **Pathfinding Algorithms:**  
  Enemies and players use A* pathfinding for movement and targeting.
- **Building and Unit Mechanics:**  
  Construct buildings, recruit units, and upgrade your forces.
- **Event System:**  
  Automated messages for clear game flow.

## Controls

- **Keyboard:**  
 Hotkeys for end turn, cycle units, selection, movement, building, and attack

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame
   ```

3. **Run the game:**
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── main.py                  # Game entry point
├── path_finding.py          # A* pathfinding logic
├── enemy_ai.py              # Enemy AI logic
├── config.py                # Game configuration and constants
├── message_box.py           # UI message boxes
├── buildings.py             # Building classes and logic
├── units.py                 # Unit classes and logic
├── assets/                  # Sprites, sounds, and other assets
└── README.md
```

---

**Developed by Sameer Nauman**
