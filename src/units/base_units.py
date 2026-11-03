import pygame
from config import *

class BaseUnits:
    # Static variable to keep track of the next available ID for units
    next_id = 1
    def __init__(self, x, y, movement, attack, defense, attack_range=1, speed=0.1, health=100, type="Unknown", loyalty=None):
        self.x = x
        self.y = y
        self.base_vision = 3
        self.health = health
        self.max_health = health
        self.movement_range = movement
        self.speed = speed
        self.attack = attack
        self.defense = defense
        self.selected = False
        # Pathfinding attributes
        self.path = []
        self.previous_position = (x,y)
        self.action_count = 0
        self.attack_range = attack_range
        self.type = type
        self.loyalty = loyalty
        self.id = BaseUnits.next_id
        BaseUnits.next_id += 1
        # Resource gathering attributes
        self.is_gathering = False
        self.is_building = False
        self.gather_resource_id = None
        self.queued = False
        self.direction = "S"

        self.update_vision_coords()

    # Update vision coordinates based on the unit's current position
    def update_vision_coords(self):
            self.vision_x = int(self.x)
            self.vision_y = int(self.y)

    # Get the vision range of the unit, considering any game multipliers
    def get_vision_range(self, game_multipliers):
        bonus = game_multipliers.get("unit_vision", 0)
        return self.base_vision + bonus
            
    def rest(self):
        self.action_count += 1

    def unit_tired(self):
        return self.action_count == 2
    
    # Use after training a unit at a building.
    def unit_queued(self):
        self.queued = True
        self.action_count = 2

    # Reset action count
    def rested(self):
        self.action_count = 0
        
    # Unit pathfinding
    def move_along_path(self):
        if self.path:
            next_x, next_y = self.path[0]

            # Update the sprite to face the tile we are currently walking toward
            self.update_direction(self.x, self.y, next_x, next_y)

            dx, dy = next_x - self.x, next_y - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < self.speed:
                self.x, self.y = next_x, next_y
                self.path.pop(0)
            else:
                self.x += self.speed * (dx / dist)
                self.y += self.speed * (dy / dist)
        
        self.update_vision_coords()

    def update_direction(self, old_x, old_y, new_x, new_y):
        if new_x > old_x:
            self.direction = "E"
        elif new_x < old_x:
            self.direction = "W"
        elif new_y > old_y:
            self.direction = "S"
        elif new_y < old_y:
            self.direction = "N"

    # Unit and unit health bar displaying
    def draw(self, screen, camera_x, camera_y, unit_sprites):
        # Sprites
        if self.selected:
            state = "selected"
        elif self.unit_tired():
            state = "rested"
        else:
            state = "normal"
        sprite_key = f"{state}_{self.direction}"

        # Normalize type key to lowercase to match UNIT_SPRITES_CONFIG ("villager", "malik_shah", etc.)
        unit_type_key = str(self.type).lower()
        
        sprite_set = unit_sprites.get(unit_type_key, {})
        
        # Safe fallback check if sprite key exists
        if sprite_key in sprite_set:
            self.sprite_to_draw = sprite_set[sprite_key]
        else:
            # Fallback to normal_S or first available sprite to prevent hard crashes
            fallback_key = "normal_S" if "normal_S" in sprite_set else (next(iter(sprite_set)) if sprite_set else None)
            if fallback_key:
                self.sprite_to_draw = sprite_set[fallback_key]
            else:
                return # Skip drawing if no sprites are loaded for this unit type

        # Isometric Math
        draw_x = self.x + OFFSET_X
        draw_y = self.y + OFFSET_Y

        screen_x = (draw_x - draw_y) * BASE_TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + camera_x
        screen_y = (draw_x + draw_y) * BASE_TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + camera_y

        # Offset to place feet on the tile
        screen_y += BASE_TILE_HEIGHT // 2

        sprite_rect = self.sprite_to_draw.get_rect()
        sprite_rect.midbottom = (screen_x, screen_y + 20)
        screen.blit(self.sprite_to_draw, sprite_rect)

        # Draw health bar only if not full health
        if self.health < self.max_health:
            bar_length = BASE_TILE_WIDTH // 2
            bar_height = 6
            bar_x = int(screen_x - bar_length // 2)
            bar_y = int(screen_y - BASE_TILE_HEIGHT // 2 - bar_height - 2)
            self.draw_health_bar(
                screen, bar_x, bar_y, bar_length, bar_height,
                self.health, self.max_health
            )
        
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