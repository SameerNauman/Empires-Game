import random

SCREEN_WIDTH, SCREEN_HEIGHT = 480, 272

# Define tile types and costs
TILE_TYPES = {"G": 1, "S": 3, "W": None}  # None = impassable

# Map dimensions
PLAYABLE_WIDTH, PLAYABLE_HEIGHT = 40, 40
BOUNDARY_WIDTH, BOUNDARY_HEIGHT = 40, 40

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
TILE_WIDTH, TILE_HEIGHT = BASE_TILE_WIDTH, BASE_TILE_HEIGHT

# Camera (no manual control anymore)
CAMERA_X, CAMERA_Y = 0, 0

DAMAGE = 0
BONUS_MULTIPLYER = 0
FLAT_BONUS = 0
