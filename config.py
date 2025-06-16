import random

SCREEN_WIDTH, SCREEN_HEIGHT = 480, 272

# Define tile types and costs
TILE_TYPES = {"G": 1, "S": 3, "W": None}  # None = impassable

# Map dimensions
PLAYABLE_WIDTH, PLAYABLE_HEIGHT = 20, 20
BOUNDARY_WIDTH, BOUNDARY_HEIGHT = 20, 20

# Create maps
PLAYABLE_MAP = [[random.choice(list(TILE_TYPES.keys())) for _ in range(PLAYABLE_WIDTH)] for _ in range(PLAYABLE_HEIGHT)]
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
