import pygame
from config import *

class PopupMenu:
    def __init__(self, options,actions, x, y, sprites, message_box, width=150, item_height=50, sprite_key="popup_menu", side="left"):
        self.options = options
        self.actions = actions #dictionary to map options to actions
        self.x = x
        self.y = y
        self.sprites = sprites
        self.message_box = message_box
        self.width = width
        self.item_height = item_height
        self.sprite_key = sprite_key
        self.side = side
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

        w, h = pygame.display.get_surface().get_size()
        self.resize(w, h)
        
        self._update_description()

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
        
        # Get the dictionary of sprites
        menu_sprites = self.sprites.get(self.sprite_key)
        spacing = 20 

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
                
            # Background
            if sprite:
                screen.blit(sprite, (self.x, item_y))
            else:
                # Fallback if sprite is missing
                pygame.draw.rect(screen, (30, 30, 30, 180), (self.x, item_y, self.width, self.item_height))
                
            # Text
            text_surf = self.font.render(option, True, text_color)
            
            text_x_offset = 15
          
            text_y_offset = 15
            
            # Blit the text relative to the sprite's current position
            screen.blit(text_surf, (self.x + text_x_offset, item_y + text_y_offset))

    def resize(self, new_width, new_height):
        spacing = 20
        total_height = (len(self.options) * self.item_height) + (max(0, len(self.options)-1) * spacing)
        
        message_box_top = new_height - self.message_box.box_height
        self.y = message_box_top - total_height - 30

        # Calculate X based on side
        if self.side == "left":
            self.x = 25
        else:
            self.x = new_width - self.width - 25 # Pin to right

    def set_position(self, x, y):
        self.x = x
        self.y = y  
        
    # Choosing an option with the awsd keys
    def move_selection(self, direction):
        if self.is_open:
            # Change the index
            self.selected_index = (self.selected_index + direction) % len(self.options)
            
            self._update_description()

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
    
    def _update_description(self):
        if not self.options:
            return

        current_text = self.options[self.selected_index]
        
        # Convert "Town Centre" -> "town_centre"
        code_key = current_text.lower().replace(" ", "_")

        desc = None
        # Check BUILDINGS (Index 7)
        if code_key in BUILDINGS:
            desc = BUILDINGS[code_key][7]
        # Check RESOURCE_BUILDINGS (Index 8)
        elif code_key in RESOURCE_BUILDINGS:
            desc = RESOURCE_BUILDINGS[code_key][8]
        else:
            self.message_box.close()

        if desc:
            self.message_box.open(desc, False)