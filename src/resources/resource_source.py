import pygame
from config import *

class ResourceSource:
    next_id = 1
    def __init__(self, x, y, resource_type, amount, building):
        self.x = x
        self.y = y
        self.resource_type = resource_type  # e.g., "wood", "gold", "food"
        self.amount = amount
        self.building = building
        self.id = ResourceSource.next_id
        ResourceSource.next_id += 1

    def is_depleted(self):
        return self.amount <= 0

    # Resource drawing
    def draw(self, screen, OFFSET_X, OFFSET_Y, camera_x, camera_y, BASE_TILE_WIDTH, BASE_TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, resource_sprites, VISIBILITY_MAP=None):
        if self.building == False:
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
            screen_x = (draw_x - draw_y) * BASE_TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + camera_x
            screen_y = (draw_x + draw_y) * BASE_TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + camera_y
            screen_y += BASE_TILE_HEIGHT // 2

            sprite = resource_sprites.get(self.resource_type)
            
            if sprite:
                rect = sprite.get_rect(midbottom=(screen_x, screen_y + BASE_TILE_HEIGHT // 2))
                screen.blit(sprite, rect)

            