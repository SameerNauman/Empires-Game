import pygame
from config import *

class PopupMenu:
    def __init__(self, options, actions, x, y, sprites, message_box, width=150, item_height=50, sprite_key="popup_menu", side="left"):
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
        self.base_side = side
        self.selected_index = 0
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 25)
        self.history = []

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
            prev_options, prev_actions = self.history.pop()
            self.open(prev_options, prev_actions, save_to_history=False)
        else:
            self.close()
            
    def close(self):
        self.is_open = False

    def resize(self, new_width, new_height):
        # 1. Calculate Heights for both styles
        spacing = 20
        y_margin = -5 # Matches the zigzag logic in draw()
        
        # Height for standard list
        standard_total_height = (len(self.options) * self.item_height) + (max(0, len(self.options)-1) * spacing)
        
        # Height for zigzag menu
        # Note: We subtract y_margin at the end because the last item doesn't need a gap below it
        v_step = self.item_height + y_margin
        zigzag_total_height = (len(self.options) * v_step) - y_margin

        # 2. Y POSITIONING
        if self.sprite_key == "building_menu":
            # We want the BOTTOM of the menu to be 150px from the screen bottom
            # So: (Screen Bottom - 150) - (Total Height of the menu)
            self.y = (new_height - 50) - zigzag_total_height
        else:
            # Anchor just above the message box
            message_box_top = new_height - self.message_box.box_height
            self.y = message_box_top - standard_total_height - 10

        # 3. X POSITIONING
        if new_width <= 1280:
            self.x = 25
        else:
            if self.side == "left":
                self.x = 25
            else:
                margin = 200
                mb_right_edge = self.message_box.box_width
                self.x = mb_right_edge - self.width + margin

    def draw(self, screen):
        if not self.is_open:
            return
        
        # 1. Get the base menu sprites (the hexagons/rectangles)
        # We look this up using the original sprite_key (e.g., 'building_menu')
        menu_sprites = self.sprites.get(self.sprite_key)
        
        # 2. Get the building icons (from the new 'building_icons' key)
        icon_map = self.sprites.get("building_icons", {})

        for i, option in enumerate(self.options):
            # --- POSITIONING ---
            if self.sprite_key == "building_menu":
                y_margin, x_margin = 0, 10
                v_step = self.item_height + y_margin
                h_step = (self.width // 2) + x_margin
                current_x_offset = h_step if i % 2 != 0 else 0
                item_x = self.x + current_x_offset
                item_y = self.y + (i * v_step)
            else:
                item_x, item_y = self.x, self.y + (i * (self.item_height + 20))

            slot_center = (item_x + self.width // 2, item_y + self.item_height // 2)

            # --- LAYER 1: DRAW THE MENU SLOT ---
            state = "selected" if i == self.selected_index else "normal"
            base_sprite = menu_sprites.get(state) if menu_sprites else None
            
            if base_sprite:
                sprite_rect = base_sprite.get_rect(center=slot_center)
                screen.blit(base_sprite, sprite_rect)
            else:
                # Fallback rect if no hexagon sprite found
                pygame.draw.rect(screen, (30, 30, 30), (item_x, item_y, self.width, self.item_height))

            # --- LAYER 2: DRAW THE BUILDING ICON ---
            icon_surface = icon_map.get(option)
            if icon_surface:
                icon_rect = icon_surface.get_rect(center=slot_center)
                screen.blit(icon_surface, icon_rect)
            
            # --- LAYER 3: DRAW TEXT (CANCEL ONLY) ---
            if option == "Cancel" or not icon_surface:
                text_color = (0, 255, 255) if i == self.selected_index else (255, 255, 255)
                text_surf = self.font.render(option, True, text_color)
                text_rect = text_surf.get_rect(center=slot_center)
                screen.blit(text_surf, text_rect)

    def move_selection(self, direction):
        if self.is_open:
            self.selected_index = (self.selected_index + direction) % len(self.options)
            self._update_description()

    def select(self):
        if self.is_open:
            selected_option = self.options[self.selected_index]
            selected_action = self.actions.get(selected_option)
            if selected_action:
                selected_action()
            return selected_option
        return None
    
    def _update_description(self):
        if not self.options: return
        current_text = self.options[self.selected_index]
        code_key = current_text.lower().replace(" ", "_")
        desc = None
        if code_key in BUILDINGS: desc = BUILDINGS[code_key][7]
        elif code_key in RESOURCE_BUILDINGS: desc = RESOURCE_BUILDINGS[code_key][8]
        else: self.message_box.close()

        if desc: self.message_box.open(desc, False)