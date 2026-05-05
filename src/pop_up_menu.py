import pygame
from config import *

class PopupMenu:
    def __init__(self, options, actions, x, y, sprites, message_box, width=150, item_height=50, sprite_key="popup_menu", side="left", state=None):
        self.options = options
        self.actions = actions
        self.x = x
        self.y = y
        self.sprites = sprites
        self.message_box = message_box
        self.width = width
        self.item_height = item_height
        self.sprite_key = sprite_key
        self.side = side
        self.state = state
        self.selected_index = 0
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 25)
        self.history = []

    # === Displaying Menus ===

    def draw(self, screen):
        if not self.is_open:
            return
        
        # Iterates through the options of the menus and positions the sprites.
        for i, option in enumerate(self.options):
            if "building_menu" in self.sprite_key:
                # Use the new Grid system for building icons
                item_x, item_y = self._get_grid_pos(i)
                self._draw_build_menu_item(screen, i, option, item_x, item_y)
            else:
                # Use the Standard Vertical system for general popups
                item_x, item_y = self._get_standard_pos(i)
                self._draw_standard_item(screen, i, option, item_x, item_y)

    # === POSITIONING METHODS ===
    
    # Calculates x and y values for the standard menu
    def _get_standard_pos(self, index):
        spacing = 20
        item_x = self.x
        item_y = self.y + (index * (self.item_height + spacing))

        return item_x, item_y

    # Calculates x and y values for the build menu
    def _get_build_menu_pos(self, index):
        x_margin = 10
        y_margin = 0
        v_step = self.item_height + y_margin
        h_step = (self.width // 2) + x_margin
        
        # Zig-zag offset
        current_x_offset = h_step if index % 2 != 0 else 0
        item_x = self.x + current_x_offset
        item_y = self.y + (index * v_step)

        return item_x, item_y

    def _get_grid_pos(self, index):
        columns = 5
        x_spacing = 20
        y_spacing = 20
        
        # 64x64 squares mean the 'step' is the size + margin
        h_step = 64 + x_spacing
        v_step = 64 + y_spacing
        
        row = index // columns
        col = index % columns
        
        # Calculate final screen position
        item_x = self.x + (col * h_step)
        item_y = self.y + (row * v_step)

        return item_x, item_y

    # === DISPLAYING METHODS ===

    # Displays the standard menu with background and text.
    def _draw_standard_item(self, screen, index, option, x, y):
        if index == self.selected_index:
            state = "selected"
        else:
            state = "normal"

        menu_sprites = self.sprites.get("popup_menu", {})
        sprite = menu_sprites.get(state)

        if sprite:
            screen.blit(sprite, (x, y))
        else:
            pygame.draw.rect(screen, (30, 30, 30), (x, y, self.width, self.item_height))

        # Text rendering
        if index == self.selected_index:
            color = (0, 255, 255)
        else:
            color = (255, 255, 255)

        text_surf = self.font.render(option, True, color)
        screen.blit(text_surf, (x + 10, y + 15))

    # Displays the build menu with hexagonal background and icons.
    def _draw_build_menu_item(self, screen, index, option, x, y, sprite_lookup="building_menu"):
        slot_center = (x + 32, y + 32)

        if index == self.selected_index:
            state = "selected"
        else:
            state = "normal"
        
        # Layer 1: The Hexagon Slot
        build_sprites = self.sprites.get(sprite_lookup, {})
        base_sprite = build_sprites.get(state)

        if base_sprite:
            rect = base_sprite.get_rect(center=slot_center)
            screen.blit(base_sprite, rect)

        # Layer 2: The Building Icon
        icon_map = self.sprites.get("building_icons", {})
        icon_surface = icon_map.get(option)
        
        if icon_surface:
            icon_rect = icon_surface.get_rect(center=slot_center)
            screen.blit(icon_surface, icon_rect)
        
        # Layer 3: Text (For 'Cancel' or if the icon is missing)
        if option == "Cancel" or not icon_surface:
            color = (0, 255, 255) if index == self.selected_index else (255, 255, 255)
            text_surf = self.font.render(option, True, color)
            text_rect = text_surf.get_rect(center=slot_center)
            screen.blit(text_surf, text_rect)

    # --- SHARED UTILITIES ---

    def open(self, options, actions, save_to_history=True):
        if save_to_history and self.options is not None:
            self.history.append((self.options, self.actions))
        self.options = options
        self.actions = actions
        self.selected_index = 0
        self.is_open = True
        self.resize(*pygame.display.get_surface().get_size())
        self._update_description()

    def resize(self, new_width, new_height):
        VIRTUAL_W = SCREEN_WIDTH 
        VIRTUAL_H = SCREEN_HEIGHT

        # Handle the Grid Menu (Building Menu)
        if "building_menu" in self.sprite_key:
            columns = 5
            x_spacing = 10
            y_spacing = 10
            
            # Anchor to the left with your 50px margin
            self.x = 40 

            # Calculate how many rows based on the options
            num_rows = ((len(self.options) - 1) // columns) + 1
            
            # Total height of the grid (64px per item + spacing)
            grid_height = num_rows * (64 + y_spacing)

            # Position Y relative to the top of the message box
            mb_top = VIRTUAL_H - self.message_box.box_height
            self.y = mb_top - grid_height - 20 # 20px padding above the box

        # Handle the Standard Menu (Vertical List)
        else:
            spacing = 20
            standard_h = (len(self.options) * self.item_height) + (max(0, len(self.options)-1) * spacing)
            
            mb_top = VIRTUAL_H - self.message_box.box_height
            if self.state == "menu":
                self.y = (VIRTUAL_H // 4) * 2.5
            else:
                self.y = mb_top - standard_h - 10
            
            # Keep standard popup menu logic
            if VIRTUAL_W <= 1280 or self.side == "left":
                self.x = 25
            else:
                self.x = VIRTUAL_W - self.width -25

    def close(self):
        self.is_open = False

    def move_selection(self, direction):
        if self.is_open:
            self.selected_index = (self.selected_index + direction) % len(self.options)
            self._update_description()

    def select(self):
        if self.is_open:
            sel = self.options[self.selected_index]
            if self.actions.get(sel): self.actions[sel]()
            return sel
        return None

    def _update_description(self):
        if not self.options: return
        
        original_name = self.options[self.selected_index]
        key = original_name.lower().replace(" ", "_")
        
        desc = None

        # Check Buildings (Index 7)
        if key in BUILDINGS:
            desc = BUILDINGS[key][7]
        # Check Resource Buildings (Index 8)
        elif key in RESOURCE_BUILDINGS:
            desc = RESOURCE_BUILDINGS[key][8]
        # Check Units (Index 9)
        elif key in UNITS:
            desc = UNITS[key][9]
        # Check Research (Index 4)
        elif key in RESEARCH:
            desc = RESEARCH[key][4]
        
        # Display or Close
        if desc: 
            self.message_box.open(desc, False)
        else: 
            self.message_box.close()