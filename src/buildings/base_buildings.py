import pygame
from config import *

class BaseBuildings:
    next_id = 1
    def __init__(self, x, y, hitpoints, population_limit=0, type="Unknown", defense=200):
        self.x = x
        self.y = y
        self.hitpoints = hitpoints
        self.max_hitpoints = hitpoints
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

        color = BUILDING_COLORS.get(self.type, (255, 255, 255))
        tired_color = tuple(max(0, c // 4) for c in color)
        if self.building_tired():
            pygame.draw.rect(screen, tired_color, (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT))
        else:
            pygame.draw.rect(screen, color, (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT))
            if self.selected:
                pygame.draw.rect(screen, (255, 255, 0), (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT), 3)
        # Draw health bar only if not full health
        if self.hitpoints < self.max_hitpoints:
            bar_length = TILE_WIDTH // 2
            bar_height = 6
            bar_x = int(screen_x - bar_length // 2)
            # Move the health bar higher so it does not overlap with unit health bars
            OFFSET_ABOVE_BUILDING = 18  # Increase this value if you want it even higher
            bar_y = int(screen_y - TILE_HEIGHT // 2 - bar_height - OFFSET_ABOVE_BUILDING)
            self.draw_health_bar(
                screen, bar_x, bar_y, bar_length, bar_height,
                self.hitpoints, self.max_hitpoints
            )

    def draw_health_bar(self, screen, x, y, length, height, current, maximum):
        GREEN = (34, 177, 76)
        INDIANRED4 = (139, 34, 34)
        BLACK = (0, 0, 0)
        current = max(0, min(current, maximum))
        filled = int(length * (current / maximum)) if maximum else 0
        pygame.draw.rect(screen, INDIANRED4, (x, y, length, height))
        if filled > 0:
            pygame.draw.rect(screen, GREEN, (x, y, filled, height))
        pygame.draw.rect(screen, BLACK, (x, y, length, height), 1)

    def rest(self):
        self.action_count += 1

    def building_tired(self):
        return self.action_count == 2
        
    def building_queued(self):
        self.queued = True
        self.action_count = 2

    def rested(self):
        self.action_count = 0

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False