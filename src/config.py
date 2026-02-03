import random
import csv, os
from resources.resource_source import ResourceSource

SCREEN_WIDTH, SCREEN_HEIGHT = 480, 272

# Define tile types and costs
TILE_DRAW_COLORS = {
    "P": (34, 177, 76),      # Plains
    "S": (193, 255, 255),    # Mountains
    "F": (34, 139, 34),      # Forest
    "H": (189, 183, 107),    # Hills
    "R": (127, 127, 127),    # Roads
    "W": (0, 162, 232),      # Water
    "FO": (128, 0, 128),     # Food (purple)
    "WO": (0, 100, 0),       # Wood (dark green)
    "GO": (255, 165, 0),     # Gold (orange)
}

TILE_TYPES = {
    "P": 2, "S": None, "F": 4, "H": 3, "R1": 1,  "R2": 1, "RC1": 1, "RC2": 1, "RC3": 1, "RC4": 1,
    "W": None, "FO": 2, "WO": 2, "GO": 2,  # You can use the same cost as plains, or None if impassable
}

ASSET_PATH = os.path.join("..", "assets", "tiles")

# Map dimensions
PLAYABLE_WIDTH, PLAYABLE_HEIGHT = 20, 20
BOUNDARY_WIDTH, BOUNDARY_HEIGHT = 20, 20

# Create maps
csv_path = os.path.join("..", "assets", "maps", "alps2.csv")
PLAYABLE_MAP = []
with open(csv_path, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        clean_row = [cell.strip() for cell in row if cell.strip()]
        if clean_row:
            PLAYABLE_MAP.append(clean_row)

# ADD THIS RIGHT AFTER LOADING
if PLAYABLE_MAP:
    PLAYABLE_MAP = [list(row) for row in zip(*PLAYABLE_MAP)]

# Resource type, amount defaults
RESOURCE_TILE_TYPES = {
    "FO": ("food", 500),
    "WO": ("wood", 400),
    "GO": ("gold", 2000),
}

resources = []

for x in range(len(PLAYABLE_MAP)):
    for y in range(len(PLAYABLE_MAP[0])):
        tile = PLAYABLE_MAP[x][y]
        if tile in RESOURCE_TILE_TYPES:
            r_type, r_amt = RESOURCE_TILE_TYPES[tile]
            resources.append(ResourceSource(x, y, r_type, r_amt))
            PLAYABLE_MAP[x][y] = "P"  # Replace with base terrain for drawing/movement


BOUNDARY_MAP = [[0 for _ in range(BOUNDARY_WIDTH)] for _ in range(BOUNDARY_HEIGHT)]

# Assuming these dimensions already exist
FOG_MAP = [[False for _ in range(PLAYABLE_HEIGHT)] for _ in range(PLAYABLE_WIDTH)]
VISIBILITY_MAP = [[0 for _ in range(PLAYABLE_HEIGHT)] for _ in range(PLAYABLE_WIDTH)]

# Centering offsets
OFFSET_X = (BOUNDARY_WIDTH - PLAYABLE_WIDTH) // 2
OFFSET_Y = (BOUNDARY_HEIGHT - PLAYABLE_HEIGHT) // 2

# Tile size and zoom
BASE_TILE_WIDTH, BASE_TILE_HEIGHT = 64, 32

DAMAGE = 0
BONUS_MULTIPLYER = 0
FLAT_BONUS = 0

# Buildings = [name, food cost, wood cost, gold cost, hitpoints, pop capacity, 1_units, 2_units, 3_units, 4_units]
BUILDINGS = {
    "town_centre": ["town_centre", 0, 400, 400, 500, 10, ["Villager", "Archers", "Spearmen"]],
}

# [name, food cost, wood cost, gold cost, hitpoints, pop capacity]
RESOURCE_BUILDINGS = {
    "mill": ["mill", 0, 50, 0, 200, 0]
}

BUILDING_COLORS = {
    "town_centre": (139, 69, 19),   # Brown
    "mill": (255, 215, 0),          # Yellow
    # Add more as you expand!
}

# [name, food cost, wood cost, gold cost, pop cost, movement, attack, defense, attack_range=1]
UNITS = {
    "Villager": ["Villager", 50, 0, 0, 1, 5, 50, 25, 1],
    "Archers": ["Archers", 60, 60, 0, 1, 7, 150, 100, 3],
    "Spearmen": ["Spearmen", 50, 50, 0, 1, 7, 100, 100, 1]
}

UNIT_COLORS = {
    "Villager": (255, 255, 255),
    "Archers": (255, 0, 0),
    "Spearmen": (0, 0, 255)
}