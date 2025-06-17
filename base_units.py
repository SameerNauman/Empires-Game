import pygame
from config import *

class BaseUnits:
    next_id = 1
    def __init__(self, x, y, movement, attack, defense, attack_range=1, speed=0.1, health=100, type="Unknown"):
        self.x = x
        self.y = y
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
        self.gather_resource_id = None
        self.queued = False

    def rest(self):
        self.action_count += 1

    def unit_tired(self):
        return self.action_count == 2
    
    def unit_queued(self):
        self.queued = True
        self.action_count = 2

    def rested(self):
        self.action_count = 0
        
    def move_along_path(self, enemy_units):
        global popup_message, popup_message_timer
        
        if self.path:
            next_x, next_y = self.path[0]
            map_x, map_y = int(next_x), int(next_y)
            if (0 <= map_x < PLAYABLE_WIDTH and 
                0 <= map_y < PLAYABLE_HEIGHT and 
                TILE_TYPES[PLAYABLE_MAP[map_x][map_y]] is None):
                popup_message = "Path blocked!"
                popup_message_timer = pygame.time.get_ticks()
                self.path = []
                return
            for enemy in enemy_units:
                if enemy.x == map_x and enemy.y == map_y:
                    popup_message = "Path blocked by enemy!"
                    popup_message_timer = pygame.time.get_ticks()
                    self.path = []
                    return
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

        color = UNIT_COLORS.get(self.type, (255, 255, 255))
        tired_color = tuple(max(0, c // 4) for c in color)
        if self.unit_tired():
            pygame.draw.circle(screen, tired_color, (int(screen_x), int(screen_y)), 5)
        else:
            pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), 5)
            if self.selected:
                pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(screen_y)), 8, 2)
        # Draw health bar only if not full health
        if self.health < self.max_health:
            bar_length = TILE_WIDTH // 2
            bar_height = 6
            bar_x = int(screen_x - bar_length // 2)
            bar_y = int(screen_y - TILE_HEIGHT // 2 - bar_height - 2)
            self.draw_health_bar(
                screen, bar_x, bar_y, bar_length, bar_height,
                self.health, self.max_health
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
