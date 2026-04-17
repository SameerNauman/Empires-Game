import pygame
from config import *

class BaseUnits:
    next_id = 1
    def __init__(self, x, y, movement, attack, defense, attack_range=1, speed=0.1, health=100, type="Unknown"):
        self.x = x
        self.y = y
        self.vision_x = int(self.x)
        self.vision_y = int(self.y)
        self.health = health
        self.max_health = health
        self.movement_range = movement
        self.speed = speed
        self.attack = attack
        self.defense = defense
        self.selected = False
        self.path = []
        self.previous_position = (x,y)
        self.action_count = 0
        self.attack_range = attack_range
        self.type = type
        self.id = BaseUnits.next_id
        BaseUnits.next_id += 1
        self.is_gathering = False
        self.is_building = False
        self.gather_resource_id = None
        self.queued = False

    
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
            dx, dy = next_x - self.x, next_y - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < self.speed:
                self.x, self.y = next_x, next_y
                self.path.pop(0)
            else:
                self.x += self.speed * (dx / dist)
                self.y += self.speed * (dy / dist)

    # Unit and unit health bar displaying
    def draw(self, screen, camera_x, camera_y, unit_sprites):
        # Sprites
        sprite_set = unit_sprites[self.type]
        self.sprite_normal = sprite_set["normal"]
        self.sprite_selected = sprite_set["selected"]

        draw_x = self.x + OFFSET_X
        draw_y = self.y + OFFSET_Y

        screen_x = (draw_x - draw_y) * BASE_TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + camera_x
        screen_y = (draw_x + draw_y) * BASE_TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + camera_y

        screen_y += BASE_TILE_HEIGHT // 2

        if self.selected:
            selected_rect = self.sprite_selected.get_rect()
            selected_rect.midbottom = (screen_x, screen_y)
            screen.blit(self.sprite_selected, selected_rect)
        else:
            sprite_rect = self.sprite_normal.get_rect()
            
            # Anchor bottom-center of sprite to the tile center
            sprite_rect.midbottom = (screen_x, screen_y)

            screen.blit(self.sprite_normal, sprite_rect)

        # color = UNIT_COLORS.get(self.type, (255, 255, 255))
        # tired_color = tuple(max(0, c // 4) for c in color)
        # if self.unit_tired():
        #     pygame.draw.circle(screen, tired_color, (int(screen_x), int(screen_y)), 5)
        # else:
        #     pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), 5)
        #     if self.selected:
        #         pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(screen_y)), 8, 2)

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