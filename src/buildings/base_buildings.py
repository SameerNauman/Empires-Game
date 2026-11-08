import pygame
from config import *

class BaseBuildings:
    # Static variable to keep track of the next available ID for buildings
    next_id = 1
    def __init__(self, x, y, hitpoints, population_limit=0, type="Unknown", defense=200, loyalty="player"):
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
        self.loyalty = loyalty
        self.id = BaseBuildings.next_id
        BaseBuildings.next_id += 1

    # Draw the building on the screen
    def draw(self, screen, camera_x, camera_y, building_sprites):
        # Normalize type key to lowercase
        bldg_type_key = str(self.type).lower()
        sprite_set = building_sprites.get(bldg_type_key, {})
        
        if not sprite_set:
            return  # Skip drawing if no sprites are found for this building type

        # Safely fetch sprite states with fallbacks
        self.sprite_normal = sprite_set.get("normal", next(iter(sprite_set.values()), None))
        self.sprite_selected = sprite_set.get("selected", self.sprite_normal)
        self.sprite_rested = sprite_set.get("rested", self.sprite_normal)

        if not self.sprite_normal:
            return

        # Calculate the screen position based on the building's grid position and camera offset
        draw_x = self.x + OFFSET_X
        draw_y = self.y + OFFSET_Y
        screen_x = (draw_x - draw_y) * BASE_TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + camera_x
        screen_y = (draw_x + draw_y) * BASE_TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + camera_y

        screen_y += BASE_TILE_HEIGHT
        
        if self.selected:
            selected_rect = self.sprite_selected.get_rect()
            selected_rect.midbottom = (screen_x, screen_y)
            screen.blit(self.sprite_selected, selected_rect)
        elif self.action_count == 1:
            rested_rect = self.sprite_rested.get_rect()
            rested_rect.midbottom = (screen_x, screen_y)
            screen.blit(self.sprite_rested, rested_rect)
        else:
            sprite_rect = self.sprite_normal.get_rect()
            sprite_rect.midbottom = (screen_x, screen_y)
            screen.blit(self.sprite_normal, sprite_rect)

        # Draw health bar
        if self.hitpoints < self.max_hitpoints:
            bar_length = BASE_TILE_WIDTH // 2
            bar_height = 6
            bar_x = int(screen_x - bar_length // 2)
            bar_y = int(screen_y - BASE_TILE_HEIGHT // 2 - bar_height - 18)
            self.draw_health_bar(screen, bar_x, bar_y, bar_length, bar_height,
                                self.hitpoints, self.max_hitpoints)

    # Health bar drawing
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
        return self.action_count == 1
    
    def building_queued(self):
        self.queued = True
        self.action_count = 1

    def rested(self):
        self.action_count = 0