import pygame
from config import *

class ResourceSource:
    next_id = 1
    def __init__(self, x, y, resource_type, amount):
        self.x = x
        self.y = y
        self.resource_type = resource_type  # e.g., "wood", "gold", "food"
        self.amount = amount
        self.id = ResourceSource.next_id
        ResourceSource.next_id += 1

    def is_depleted(self):
        return self.amount <= 0

    # Resource drawing
    def draw(self, screen, OFFSET_X, OFFSET_Y, CAMERA_X, CAMERA_Y, TILE_WIDTH, TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, resources, VISIBILITY_MAP=None):
        # Only draw if tile is visible
        visible = True
        if VISIBILITY_MAP is not None:
            if 0 <= self.x < len(VISIBILITY_MAP) and 0 <= self.y < len(VISIBILITY_MAP[0]):
                visible = VISIBILITY_MAP[self.x][self.y] == 2
            else:
                visible = False
        if not visible:
            return

        draw_x = self.x + OFFSET_X
        draw_y = self.y + OFFSET_Y
        screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + CAMERA_X
        screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + CAMERA_Y
        screen_y += TILE_HEIGHT // 2

        # Draw this resource only once, not for every resource in the list
        if self.resource_type == "food":
            pygame.draw.circle(screen, (128, 0, 128), (int(screen_x), int(screen_y)), 10)
        elif self.resource_type == "gold":
            pygame.draw.circle(screen, (255, 165, 0), (int(screen_x), int(screen_y)), 10)
        else:
            pygame.draw.circle(screen, (0, 100, 0), (int(screen_x), int(screen_y)), 10)