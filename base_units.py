import pygame
from config import *

class BaseUnits:
    def __init__(self, x, y, movement, attack, defense, speed=0.1, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.movement_range = movement
        self.speed = speed
        self.attack = attack
        self.defense = defense
        self.selected = False
        self.path = []
        self.previous_position = (x,y)
        self.action_count = 0
        self.enemy_range = 1

    def rest(self):
        self.action_count += 1

    def unit_tired(self):
        if self.action_count == 2:
            return True
        else:
            return False
    
    def rested(self):
        self.action_count = 0
        
    def move_along_path(self, enemy_units):
        global popup_message, popup_message_timer
        
        if self.path:
            next_x, next_y = self.path[0]
            
            # Convert to integer for map lookup
            map_x, map_y = int(next_x), int(next_y)
            
            # Verify the tile is still passable
            if (0 <= map_x < PLAYABLE_WIDTH and 
                0 <= map_y < PLAYABLE_HEIGHT and 
                TILE_TYPES[PLAYABLE_MAP[map_x][map_y]] is None):
                popup_message = "Path blocked!"
                popup_message_timer = pygame.time.get_ticks()
                self.path = []
                return
            
            # NEW CODE: Check if the tile is occupied by an enemy unit
            for enemy in enemy_units:
                if enemy.x == map_x and enemy.y == map_y:
                    popup_message = "Path blocked by enemy!"
                    popup_message_timer = pygame.time.get_ticks()
                    self.path = []
                    return
            
        # Rest of movement code...
            dx, dy = next_x - self.x, next_y - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < self.speed:
                self.x, self.y = next_x, next_y
                self.path.pop(0)
            else:
                self.x += self.speed * (dx / dist)
                self.y += self.speed * (dy / dist)

    def draw(self, screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT):
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + camera_x
        screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + camera_y
        screen_y += TILE_HEIGHT // 2

        if self.unit_tired() == True:
            pygame.draw.circle(screen, (64, 64, 64), (int(screen_x), int(screen_y)), 5)
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(screen_x), int(screen_y)), 5)
            if self.selected:
                pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(screen_y)), 8, 2)