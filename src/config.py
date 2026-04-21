import random
import csv, os
from resources.resource_source import ResourceSource

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

# Map dimensions
PLAYABLE_WIDTH, PLAYABLE_HEIGHT = 20, 20
BOUNDARY_WIDTH, BOUNDARY_HEIGHT = 20, 20

# Mini Map dimensions and position
MINIMAP_SIZE = 400

# Calculate scaled tile size to fit map in mini map area
MINI_TILE = 18
HALF_WIDTH = MINI_TILE // 2
HALF_HEIGHT = MINI_TILE // 4
RADIUS = MINIMAP_SIZE // 2
SMALLER_RADIUS = int(RADIUS * 0.85)

# Top-down view scale (no isometric compression) - reduced size (0.40 is the multiplier)
MINI_MAP_SCALE = int(RADIUS // (PLAYABLE_WIDTH // 2 + 1) * 0.40)

# For proper isometric centering:
# - Center X is where (x - y) = 0, so offset_draw_x should be at circle center
# - Center Y is where (x + y) is at midpoint (PLAYABLE_HEIGHT - 1 for 20x20 map)
# The isometric grid's center point is at screen coords (0, (PLAYABLE_HEIGHT-1) * half_height)
# We want this at (radius, radius)
OFFSET_DRAW_X = RADIUS
OFFSET_DRAW_Y = RADIUS - (PLAYABLE_HEIGHT - 1) * HALF_HEIGHT
CENTER_X = SCREEN_WIDTH - RADIUS - 10
CENTER_Y = SCREEN_HEIGHT - RADIUS - 10

# Define tile types and costs

TERRAIN_SPRITES = {
            "P": "grass4.png",
            "F3": "forest3.png",
            "F4": "forest4.png",
            "R1": "road1.png",
            "R2": "road2.png",
            "RC1": "roadcorner1.png",
            "RC2": "roadcorner2.png",
            "RC3": "roadcorner3.png",
            "RC4": "roadcorner4.png",
            "H": "hills2.png",
            "W1": "river1.png",
            "W2": "river2.png",
            "W3": "river3.png",
            "W4": "river4.png",
            "WC1": "rivercorner1.png",
            "WC2": "rivercorner2.png",
            "WC3": "rivercorner3.png",
            "WC4": "rivercorner4.png",
            "M": "mountain1.png",
            "M2": "mountain2.png"            
        }

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
    "P": 2, "F3": 4, "F4": 4, "H": 3, "R1": 1,  "R2": 1, "RC1": 1, "RC2": 1, "RC3": 1, "RC4": 1,
    "FO": 2, "WO": 2, "GO": 2,  # Same cost as plains, or None if impassable
}

TERRAIN_PATH = os.path.join("..", "assets", "terrain2")

# The base path for all unit assets
UNIT_ASSETS_BASE = os.path.join("..", "assets", "units")

UNIT_SPRITES_CONFIG = {
    "Basil": {
        "folder": "basil",
        "files": {
            "normal_N": "basil_N.png",
            "normal_S": "basil_S.png",
            "normal_E": "basil_E.png",
            "normal_W": "basil_W.png",
            "selected_N": "selected_N.png",
            "selected_S": "selected_S.png",
            "selected_E": "selected_E.png",
            "selected_W": "selected_W.png"
        }
    },
    "Villager": {
        "folder": "villager",
        "files": {
            "normal_N": "villager_N.png",
            "normal_S": "villager_S.png",
            "normal_E": "villager_E.png",
            "normal_W": "villager_W.png",
            "selected_N": "selected_N.png",
            "selected_S": "selected_S.png",
            "selected_E": "selected_E.png",
            "selected_W": "selected_W.png"
        }
    },
    "Archers": {
        "folder": "archer2",
        "files": {
            "normal_N": "archer_N.png",
            "normal_S": "archer_S.png",
            "normal_E": "archer_E.png",
            "normal_W": "archer_W.png",
            "selected_N": "selected_N.png",
            "selected_S": "selected_S.png",
            "selected_E": "selected_E.png",
            "selected_W": "selected_W.png"
        }
    }
}

BUILDING_PATH = os.path.join("..", "assets", "buildings3")

BUILDING_SPRITES = {
    "town_centre": {
        "normal": "towncentre.png",
        "selected": "tc_selected.png"
    },
    "market": {
        "normal": "market.png",
        "selected": "market_selected.png"
    },
    "mill": {
        "normal": "mill.png",
        "selected": "mill_selected.png"
    },
    "farm": {
        "normal": "farm.png",
        "selected": "farm.png"
    }
}

RESOURCES_PATH = os.path.join("..", "assets", "resources")

RESOURCE_SPRITES = {
    "food": "berry_bush.png",
    "wood": "tree4.png",
    "gold": "gold2.png"
}

# Resource type, amount defaults
RESOURCE_TILE_TYPES = {
    "FO": ("food", 500),
    "WO": ("wood", 400),
    "GO": ("gold", 2000)
}

RESOURCE_ICONS_PATH = os.path.join("..", "assets", "resource_icons")

# filename, x, y, rows, cols
RESOURCE_ICONS = {
    "food": ["bread.png", (SCREEN_WIDTH - 300), 100, 1, 18],
    "wood": ["wood.png", (SCREEN_WIDTH - 200), 97, 1, 34],
    "gold": ["gold.png", (SCREEN_WIDTH - 100), 100, 1, 24]
}

# --- STEP 1: LOAD TERRAIN MAP ---
MAP_CSV = os.path.join("..", "assets", "maps", "alps4.csv")
PLAYABLE_MAP = []
with open(MAP_CSV, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        # Load exactly as is; these should now only be P, H, M, W, etc.
        clean_row = [cell.strip() for cell in row if cell.strip()]
        if clean_row:
            PLAYABLE_MAP.append(clean_row)

# Transpose for [x][y] access
if PLAYABLE_MAP:
    PLAYABLE_MAP = [list(row) for row in zip(*PLAYABLE_MAP)]

# --- STEP 2: LOAD RESOURCE OVERLAY ---
RESOURCE_CSV = os.path.join("..", "assets", "maps", "resources.csv")
resources = []
with open(RESOURCE_CSV, newline='') as csvfile:
    reader = csv.reader(csvfile)
    resource_data = []
    for row in reader:
        # Keep empty cells as None or empty strings to maintain grid alignment
        resource_data.append([cell.strip() for cell in row])

# Transpose resource map to match terrain map [x][y]
if resource_data:
    resource_data = [list(row) for row in zip(*resource_data)]

# --- STEP 3: POPULATE RESOURCE OBJECTS ---
# Iterate through the resource_data grid
for x in range(len(resource_data)):
    for y in range(len(resource_data[0])):
        tile = resource_data[x][y]
        
        # Check if this cell in the resource map contains a valid resource code
        if tile in RESOURCE_TILE_TYPES:
            r_type, r_amt = RESOURCE_TILE_TYPES[tile]
            
            # Create the resource source at these coordinates
            # It will now sit "on top" of whatever is in PLAYABLE_MAP[x][y]
            resources.append(ResourceSource(x, y, r_type, r_amt, False))

BOUNDARY_MAP = [[0 for _ in range(BOUNDARY_WIDTH)] for _ in range(BOUNDARY_HEIGHT)]

# Assuming these dimensions already exist
FOG_MAP = [[False for _ in range(PLAYABLE_HEIGHT)] for _ in range(PLAYABLE_WIDTH)]
VISIBILITY_MAP = [[0 for _ in range(PLAYABLE_HEIGHT)] for _ in range(PLAYABLE_WIDTH)]

# Centering offsets
OFFSET_X = (BOUNDARY_WIDTH - PLAYABLE_WIDTH) // 2
OFFSET_Y = (BOUNDARY_HEIGHT - PLAYABLE_HEIGHT) // 2

# Camera
MARGIN = 50
SCROLL_SPEED = 10

# Tile size and zoom
BASE_TILE_WIDTH, BASE_TILE_HEIGHT = 128, 64

DAMAGE = 0
BONUS_MULTIPLYER = 0
FLAT_BONUS = 0

# Buildings = [name, food cost, wood cost, gold cost, hitpoints, pop capacity, 1_units, 2_units, 3_units, 4_units]
BUILDINGS = {
    "town_centre": ["town_centre", 0, 400, 400, 500, 10, ["Villager"]],
    "market": ["market", 0, 100, 100, 200, 0]
}

# [name, food cost, wood cost, gold cost, hitpoints, pop capacity, resource type, resource amount]
RESOURCE_BUILDINGS = {
    "mill": ["mill", 0, 50, 0, 200, 0, "food", 500000],
    "farm": ["farm", 0, 50, 0, 100, 0, "food", 500000]
}

# BUILDING_COLORS = {
#     "town_centre": (139, 69, 19),   # Brown
#     "mill": (255, 215, 0),          # Yellow
#     # Add more as you expand!
# }

BASIL_DESC = ("Basil II is the Emperor of the Byzantine Empire. He is a cavalry unit that can move long distances. \n\n" "300 / 300")

VILLAGER_DESC = ("Villagers gather resources and construct buildings. They are weak in combat but essential for your economy. \n\n" "50 / 25")

ARCHER_DESC = ("Archers are ranged units that can attack from a distance. \n" 
"Equipped with bows, and leather armor. \n\n" "150 / 100")

SPEARMEN_DESC = ("Spearmen are melee units that excel at defending against cavalry.\n"
"Equipped with spears, and leather armor. \n\n" "100 / 100")

# [name, food cost, wood cost, gold cost, pop cost, movement, attack, defense, attack_range=1, description=""]
UNITS = {
    "Basil": ["Basil", 300, 0, 300, 1, 10, 300, 300, 1, BASIL_DESC],
    "Villager": ["Villager", 50, 0, 0, 1, 5, 50, 25, 1, VILLAGER_DESC],
    "Archers": ["Archers", 60, 60, 0, 1, 7, 150, 100, 3, ARCHER_DESC],
    "Spearmen": ["Spearmen", 50, 50, 0, 1, 7, 100, 100, 1, SPEARMEN_DESC]
}

UNIT_COLORS = {
    "Villager": (255, 255, 255),
    "Archers": (255, 0, 0),
    "Spearmen": (0, 0, 255)
}