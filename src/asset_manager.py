import pygame
import os
from animated_sprite import AnimatedSprite
from config import *

class AssetManager:
    def __init__(self):
        # Sprite dictionaries to hold loaded assets for terrain, units, and buildings
        self.terrain_sprites = {}
        self.unit_sprites = {}
        self.building_sprites = {}
        self.building_icons = {}
        self.resource_sprites = {}
        self.resource_animations = {}
        self.ui_elements = {}
        self.animated_sprites = {}

        self.load_all_assets()

        # Day counter sprite
        self.day_counter_anim = AnimatedSprite(
            os.path.join(UI_ELEMENTS_PATH, "day_counter.png"), 
            rows=1, 
            cols=22, 
            animation_speed=0.10 
        )

    # Loads all assets by calling individual loading methods for each asset type
    def load_all_assets(self):
        self.load_terrain_sprites()        
        self.load_unit_sprites()     
        self.load_building_sprites()
        self.load_building_icons()
        self.load_resource_sprites()
        self.load_resource_icons()
        self.load_ui_elements()
        self.load_animated_screens()

    # Loads the sprites for the world tiles
    def load_terrain_sprites(self):
        for tile_code, filename in TERRAIN_SPRITES.items():
            path = os.path.join(TERRAIN_PATH, filename)
            self.terrain_sprites[tile_code] = pygame.image.load(path).convert_alpha()
    
    # loads the sprites for the units
    def load_unit_sprites(self):
        for unit_name, config in UNIT_SPRITES_CONFIG.items():
            unit_folder = config["folder"]
            self.unit_sprites[unit_name] = {}  # Assign directly to self.unit_sprites!
            
            for key, filename in config["files"].items():
                full_path = os.path.join(UNIT_ASSETS_BASE, unit_folder, filename)
                self.unit_sprites[unit_name][key] = pygame.image.load(full_path).convert_alpha()

    # Loads the sprites for the buildings
    def load_building_sprites(self):
        for building_type, sprite_info in BUILDING_SPRITES.items():

            # If this building has multiple sprite states (normal, selected, etc.)
            if isinstance(sprite_info, dict):
                self.building_sprites[building_type] = {
                    key: pygame.image.load(os.path.join(BUILDING_PATH, filename)).convert_alpha()
                    for key, filename in sprite_info.items()
                }

            # Backwards compatibility: single-sprite buildings
            else:
                path = os.path.join(BUILDING_PATH, sprite_info)
                self.building_sprites[building_type] = pygame.image.load(path).convert_alpha()

    # Loads the icons for the buildings
    def load_building_icons(self):
        for building_name, filename in BUILDING_ICONS.items():
            # Build the full path
            full_path = os.path.join(BUILDING_ICONS_PATH, filename)
            try:
                # Load and convert for better performance
                sprite = pygame.image.load(full_path).convert_alpha()
                self.building_icons[building_name] = sprite
            except pygame.error as e:
                print(f"Unable to load icon {filename} from {BUILDING_ICONS_PATH}: {e}")
                
    # Loads the sprites for the resources
    def load_resource_sprites(self):
        for res_type, filename in RESOURCE_SPRITES.items():
            full_path = os.path.join(RESOURCES_PATH, filename)
            self.resource_sprites[res_type] = pygame.image.load(full_path).convert_alpha()

    # loads the sprites for ui resource icons
    def load_resource_icons(self):
        for res_type, data in RESOURCE_ICONS.items():
            filename = data[0]
            full_path = os.path.join(RESOURCE_ICONS_PATH, filename)

            rows = data[3]
            cols = data[4]
            
            self.resource_animations[res_type] = AnimatedSprite(full_path, rows, cols)

    # Loads the sprites for the UI elements
    def load_ui_elements(self):
        for element_name, data in UI_ELEMENTS.items():
            # Check if it's a dictionary (like your popup_menu)
            if isinstance(data, dict):
                self.ui_elements[element_name] = {}
                for state, filename in data.items():
                    full_path = os.path.join(UI_ELEMENTS_PATH, filename)
                    self.ui_elements[element_name][state] = pygame.image.load(full_path).convert_alpha()
            else:
                # It's a regular string (like message_box)
                full_path = os.path.join(UI_ELEMENTS_PATH, data)
                self.ui_elements[element_name] = pygame.image.load(full_path).convert_alpha()

    # Loads the animated screens from the ANIMATED_SCREENS dictionary and creates AnimatedSprite objects for each screen.
    def load_animated_screens(self):
        
        for name, data in ANIMATED_SCREENS.items():
            filename = data[0]
            full_path = os.path.join(SCREENS_PATH, filename)

            rows = data[3]
            cols = data[4]

            # Create an AnimatedSprite object for the screen and store it in self.animated_sprites
            self.animated_sprites[name] = AnimatedSprite(full_path, rows, cols)