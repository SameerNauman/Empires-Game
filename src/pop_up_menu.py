import pygame
from config import *

class PopupMenu:
    def __init__(self, options,actions, x, y, sprites, width=150, item_height=50):
        self.options = options
        self.actions = actions #dictionary to map options to actions
        self.x = x
        self.y = y
        self.sprites = sprites
        self.width = width
        self.item_height = item_height
        self.selected_index = 0
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 25)

        self.history = []  # Stack to keep track of menu history for nested menus

    def open(self, options, actions, save_to_history=True):
        if save_to_history and self.options is not None:
            self.history.append((self.options, self.actions))
        self.options = options
        self.actions = actions
        self.selected_index = 0
        self.is_open = True

    def back(self):
        if self.history:
            # Pop the last menu state from history
            prev_options, prev_actions = self.history.pop()
            # Open it without saving the current (bad) state to history
            self.open(prev_options, prev_actions, save_to_history=False)
        else:
            self.is_open = False # Close if no history remains
            
    def close(self):
        self.is_open = False
        self.menu_type = None

    def draw(self, screen):
        if not self.is_open:
            return
        
        # 1. Get the dictionary of sprites
        menu_sprites = self.sprites.get("popup_menu")
        spacing = 40 

        for i, option in enumerate(self.options):
            # Calculate the Y position for this specific menu item slot
            item_y = self.y + (i * (self.item_height + spacing))
            
            # Determine state-based visuals
            if i == self.selected_index:
                sprite = menu_sprites.get("selected") if menu_sprites else None
                text_color = (0, 255, 255) # Cyan highlight
            else:
                sprite = menu_sprites.get("normal") if menu_sprites else None
                text_color = (255, 255, 255) # Standard white
                
            # --- DRAW BACKGROUND ---
            if sprite:
                screen.blit(sprite, (self.x, item_y))
            else:
                # Fallback if sprite is missing
                pygame.draw.rect(screen, (30, 30, 30, 180), (self.x, item_y, self.width, self.item_height))
                pygame.draw.rect(screen, (255, 255, 255), (self.x, item_y, self.width, self.item_height), 1)
                
            # --- DRAW CENTERED TEXT ---
            text_surf = self.font.render(option, True, text_color)
            
            # Horizontal Centering: (Total Width - Text Width) / 2
            text_x_offset = 15
            
            # Vertical Centering: (Total Height - Text Height) / 2
            text_y_offset = 15
            
            # Blit the text relative to the sprite's current position
            screen.blit(text_surf, (self.x + text_x_offset, item_y + text_y_offset))

    def set_position(self, x, y):
        self.x = x
        self.y = y  
        
    # Choosing an option with the awsd keys
    def move_selection(self, direction):
        if self.is_open:
            self.selected_index = (self.selected_index + direction) % len(self.options)

    def select(self):
        if self.is_open:
            selected_option = self.options[self.selected_index]
            selected_action = self.actions.get(selected_option)
            if selected_action:
                selected_action()  # Call the selected action
            else:
                print(f"WARNING: No action defined for '{selected_option}'")
            return selected_option
        return None