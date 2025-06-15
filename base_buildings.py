import pygame
from config import *

class BaseBuildings:
    next_id = 1
    def __init__(self, x, y, hitpoints, population_limit=0, type="Unknown", defense=200):
        self.x = x
        self.y = y
        self.hitpoints = hitpoints
        self.population_limit = population_limit
        self.queued = False
        self.is_constructed = False
        self.selected = False
        self.action_count = 0
        self.type = type
        self.defense = defense
        self.id = BaseBuildings.next_id
        BaseBuildings.next_id += 1

    def draw(self, screen, OFFSET_X, OFFSET_Y, CAMERA_X, CAMERA_Y, TILE_WIDTH, TILE_HEIGHT):
        draw_x = self.x + OFFSET_X
        draw_y = self.y + OFFSET_Y
        screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + CAMERA_X
        screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + CAMERA_Y
        screen_y += TILE_HEIGHT // 2

        if self.building_tired() == True:
            pygame.draw.rect(screen, (64, 64, 64), (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT))
        else:
            pygame.draw.rect(screen, (255, 255, 255), (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT))
            if self.selected:
                pygame.draw.rect(screen, (255, 255, 0), (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT), 3)

    def rest(self):
        self.action_count += 1

    def building_tired(self):
        if self.action_count == 2:
            return True
        else:
            return False
        
    def building_queued(self):
        self.queued = True
        self.action_count = 2

    def rested(self):
        self.action_count = 0

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False
