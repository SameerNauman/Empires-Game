import pygame
import os
from animated_sprite import AnimatedSprite
from config import *

class AssetManager:
    def __init__(self, pfaction, efaction, pcolor, ecolor):
        # Sprite dictionaries to hold loaded assets for terrain, units, and buildings
        self.terrain_sprites = {}
        self.punit_sprites = {}
        self.eunit_sprites = {}
        self.pbuilding_sprites = {}
        self.ebuilding_sprites = {}
        self.building_icons = {}
        self.resource_sprites = {}
        self.resource_animations = {}
        self.ui_elements = {}
        self.animated_sprites = {}

        self.pfaction = pfaction
        self.efaction = efaction
        self.pcolor = pcolor
        self.ecolor = ecolor

        self.load_all_assets()

        # Day counter sprite
        self.day_counter_anim = AnimatedSprite(
            os.path.join(UI_ELEMENTS_PATH, "day_counter.png"), 
            rows=1, 
            cols=22, 
            animation_speed=0.10 
        )

    def reload_factions(self, pfaction, efaction, pcolor, ecolor):
        self.pfaction = pfaction
        self.efaction = efaction
        self.pcolor = pcolor
        self.ecolor = ecolor
        
        # Clear old dictionaries and reload
        self.punit_sprites.clear()
        self.eunit_sprites.clear()
        self.pbuilding_sprites.clear()
        self.ebuilding_sprites.clear()
        
        self.load_faction_assets()

    # Loads all assets by calling individual loading methods for each asset type
    def load_all_assets(self):
        self.load_terrain_sprites()      
        self.load_faction_assets()
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
    
    def load_faction_assets(self):
        # Load Player Faction Assets (Defaulting to "Dark Age" or checking available ages per faction)
        self._load_side_assets(self.pfaction, self.pcolor, is_player=True)
        
        # Load Enemy Faction Assets
        self._load_side_assets(self.efaction, self.ecolor, is_player=False)

    def _load_side_assets(self, faction_key, color_key, is_player):
        target_unit_dict = self.punit_sprites if is_player else self.eunit_sprites
        target_building_dict = self.pbuilding_sprites if is_player else self.ebuilding_sprites

        faction_data = FACTIONS.get(faction_key, {})
        
        age_configs = [
            (key, value)
            for key, value in faction_data.items()
            if isinstance(value, dict) and ("units" in value or "buildings" in value)
        ]
        if not age_configs and ("units" in faction_data or "buildings" in faction_data):
            age_configs = [("Dark Age", faction_data)]

        for age_name, value in age_configs:
            age_folder = age_name.lower().replace(" ", "_")
            base_path = os.path.join("..", "assets", "factions", faction_key, color_key, age_folder)

            # --- Load Units for this Age ---
            if "units" in value:
                for unit_name, unit_data in value["units"].items():
                    unit_folder = unit_data.get("folder", unit_name)
                    target_unit_dict[unit_name] = {}
                    
                    files = unit_data.get("files", {})
                    for file_key, filename in files.items():
                        full_path = os.path.join(base_path, "units", unit_folder, filename)
                        if os.path.exists(full_path):
                            target_unit_dict[unit_name][file_key] = pygame.image.load(full_path).convert_alpha()

            # --- Load Buildings for this Age ---
            if "buildings" in value:
                for bldg_name, bldg_data in value["buildings"].items():
                    bldg_folder = bldg_data.get("folder", bldg_name)
                    target_building_dict[bldg_name] = {}
                    
                    files = bldg_data.get("files", {})
                    for file_key, filename in files.items():
                        full_path = os.path.join(base_path, "buildings", bldg_folder, filename)
                        if os.path.exists(full_path):
                            target_building_dict[bldg_name][file_key] = pygame.image.load(full_path).convert_alpha()

    # Loads the icons for the buildings
    def load_building_icons(self):
        for building_name, filename in BUILDING_ICONS.items():
            full_path = os.path.join(BUILDING_ICONS_PATH, filename)
            try:
                sprite = pygame.image.load(full_path).convert_alpha()
                self.building_icons[building_name] = sprite
            except pygame.error as e:
                print(f"Unable to load icon {filename} from {BUILDING_ICONS_PATH}: {e}")

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