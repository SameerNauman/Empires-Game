import pygame
from units.base_units import BaseUnits
from buildings.base_buildings import BaseBuildings
from resources.resource_source import ResourceSource
from message_box import MessageBox
from pop_up_menu import PopupMenu
from path_finding import PathFinding
from target_aquisition import TargetAquisition
from enemy_ai import EnemyAi
from animated_sprite import AnimatedSprite
from config import *

class GameplayState:
    def __init__(self, screen, game_state_manager):
        self.game_state_manager = game_state_manager
        self.screen = screen
        w, h = screen.get_size()
        self.clock = pygame.time.Clock()
        self.selected_tile = (4, 4)
        self.hovered_tile = self.selected_tile
        self.path = []
        self.is_moving = False
        self.tactical_map_mode = False
        self.last_key_pressed = None
        self.reachable_tiles = set()
        self.food_amount = 500
        self.wood_amount = 500
        self.gold_amount = 500
        self.enemy_food = 500
        self.enemy_wood = 500
        self.enemy_gold = 500
        self.selected_unit = None
        self.selected_building = None
        self.selected_unit_id = None
        self.selected_building_id = None
        self.running = True
        self.camera_x = 0
        self.camera_y = 0
        self.free_cam_active = False
        self.camera_return = False
        self.camera_target_x = 0
        self.camera_target_y = 0
        self.tile_move_delay = 5

        self.minimap_size = int(h * 0.42)
        self.radius = self.minimap_size // 2
        self.smaller_radius = int(self.radius * 0.85)
        
        # Scale and positioning
        self.mini_map_scale = int(self.radius // (PLAYABLE_WIDTH // 2 + 1) * 0.40)
        self.mini_map_center_x = w - self.radius - 20
        self.mini_map_center_y = h - self.radius - 20

        # Research
        self.researched_techs = set()
        self.tech_multipliers = {
            "unit_vision": 0,
            "unit_movement": 0,
            "building_vision": 0,
            "gather_rate_food": 1.0,
            "gather_rate_wood": 1.0,
            "gather_rate_gold": 1.0
        }
        self.pending_techs = []

        # Terrain sprites
        self.terrain_sprites = {}
        self.terrain_path = TERRAIN_PATH
        self.load_terrain_sprites()

        # Unit sprites
        self.unit_sprites = {}
        self.unit_sprites = self.load_unit_sprites()

        # Building sprites
        self.building_sprites = {}
        self.building_path = BUILDING_PATH
        self.load_building_sprites()

        # Resource sprites
        self.load_resource_sprites()
        
        self.load_building_icons()

        # Resource icons
        self.load_resource_icons()

        # UI elements
        self.load_ui_elements()

        # Attack
        self.target_select_mode = False
        self.targetable_enemies = []
        self.selected_target_index = 0

        # Player units initialization
        # basil = BaseUnits(3, 3, 10, 300, 300, 1, type="Basil")
        villager = BaseUnits(3, 3, 10, 300, 300, 1, type="Villager")
        # Player buildings initialization
        town_centre = BaseBuildings(3, 3, 500, 10, type="town_centre")
        town_centre.is_constructed = True
        # Enemy units initialization
        enemy_villager = BaseUnits(6, 10, 5, 50, 25, 1, type="Villager")
        # Enemy buildings initialization
        e_town_centre = BaseBuildings(6, 10, 500, 10, type="town_centre")
        e_town_centre.is_constructed = True

        # Player unit and building lists
        self.units = [villager]
        self.buildings = [town_centre]
        self.resources = resources
        self.construction = {}
        # Enemy unit and building lists
        self.enemy_units = [enemy_villager]
        self.e_buildings = [e_town_centre]
        self.population = len(self.units)

        # Turn control
        self.player_turn = True
        self.enemy_moving = False
        self.enemy_paths_planned = False
        self.enemy_turn_index = 0      # index of the current enemy being processed
        self.enemy_turn_phase = 'move' # 'move', 'attack', or 'done'
        self.enemy_turn_delay = 0      # delay timer for animation

        self.game_over = False
        
        # Updates the unit visibility
        self.update_VISIBILITY_MAP()

        self.message_box = MessageBox(
            self.screen, 
            SCREEN_WIDTH, 
            SCREEN_HEIGHT, 
            self.ui_elements["message_box"] # Pass the loaded sprite here
        )
        self.error_message = True

        self.popup_menu = PopupMenu(
            [], {}, 0, 0, self.ui_elements, self.message_box, 
            sprite_key="popup_menu", side="left"
        )
        self.building_menu = PopupMenu(
            [], {}, 0, 0, self.ui_elements, self.message_box, 
            sprite_key="building_menu", side="right"
        )
        
        self.target_aquisition = TargetAquisition()
        self.enemy_ai = EnemyAi(self.enemy_units)

# === WORLD DISPLAYING ===

    # Removes fog of war around player units and buildings according to their vision range
    def update_VISIBILITY_MAP(self):
        # Reset current visibility
        for x in range(len(VISIBILITY_MAP)):
            for y in range(len(VISIBILITY_MAP[0])):
                if VISIBILITY_MAP[x][y] == 2:
                    VISIBILITY_MAP[x][y] = 1

        # Update from Units
        for unit in self.units:
            ux, uy = unit.vision_x, unit.vision_y
            v_range = unit.get_vision_range(self.tech_multipliers)
            self.apply_vision_circle(ux, uy, v_range)

        # Update from Buildings
        building_bonus = self.tech_multipliers.get("building_vision", 0)
        base_building_vision = 3
        
        for building in self.buildings:
            if building.is_constructed:
                bx, by = int(building.x), int(building.y)
                self.apply_vision_circle(bx, by, base_building_vision + building_bonus)

    def apply_vision_circle(self, cx, cy, radius):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    tx, ty = cx + dx, cy + dy
                    if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                        VISIBILITY_MAP[tx][ty] = 2

    # Displays the sprites for the terrain, and magenta for missing sprites
    def draw_map_with_fog(self, map_data, VISIBILITY_MAP):
        for tx in range(len(map_data)):
            for ty in range(len(map_data[tx])):

                # Skip unseen tiles
                if VISIBILITY_MAP[tx][ty] == 0:
                    continue

                draw_tx, draw_ty = self.draw_coords(tx, ty)
                screen_x, screen_y = self.screen_coords(draw_tx, draw_ty)

                tile = map_data[tx][ty]

                # Sprite aquisition
                sprite = self.terrain_sprites.get(tile)

                if sprite:
                    # Darken if explored but not currently visible
                    if VISIBILITY_MAP[tx][ty] == 1:
                        sprite = sprite.copy()
                        sprite.fill(
                            (120, 120, 120, 255),
                            special_flags=pygame.BLEND_RGBA_MULT
                        )

                    self.screen.blit(
                        sprite,
                        (screen_x - BASE_TILE_WIDTH // 2, screen_y)
                    )

                else:
                    # If there isnt a sprite, draw a magenta tile
                    pygame.draw.polygon(
                        self.screen,
                        (255, 0, 255),
                        [
                            (screen_x, screen_y),
                            (screen_x + BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),
                            (screen_x, screen_y + BASE_TILE_HEIGHT),
                            (screen_x - BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),
                        ],
                    )

    # Loads the sprites for the world tiles
    def load_terrain_sprites(self):
        for tile_code, filename in TERRAIN_SPRITES.items():
            path = os.path.join(self.terrain_path, filename)
            self.terrain_sprites[tile_code] = pygame.image.load(path).convert_alpha()
    
    # loads the sprites for the units
    def load_unit_sprites(self):
        loaded_sprites = {}
    
        for unit_name, config in UNIT_SPRITES_CONFIG.items():
            unit_folder = config["folder"]
            loaded_sprites[unit_name] = {}
            
            for key, filename in config["files"].items():
                # Combine: ../assets/units/ + folder_name + filename
                full_path = os.path.join(UNIT_ASSETS_BASE, unit_folder, filename)
                
                # Load the surface (assuming Pygame)
                loaded_sprites[unit_name][key] = pygame.image.load(full_path).convert_alpha()
                
        return loaded_sprites

    # Draws player and enemy units
    def display_units(self):
        # Create a combined list of all units that should be drawn
        units_to_draw = []

        # Add player units
        units_to_draw.extend(self.units)

        # Add enemy units only if they are visible
        for enemy in self.enemy_units:
            ex, ey = int(enemy.x), int(enemy.y)
            if (0 <= ex < len(VISIBILITY_MAP) and 
                0 <= ey < len(VISIBILITY_MAP[0]) and 
                VISIBILITY_MAP[ex][ey] == 2):
                units_to_draw.append(enemy)

        #Sort the COMBINED list by the Z-axis (x + y)
        # Units with smaller x+y (further away) come first in the list
        units_to_draw.sort(key=lambda u: u.x + u.y)

        # Draw them all in a single pass
        for unit in units_to_draw:
            unit.draw(
                self.screen, 
                self.camera_x, 
                self.camera_y, 
                self.unit_sprites
            )

    # Loads the sprites for the buildings
    def load_building_sprites(self):
        for building_type, sprite_info in BUILDING_SPRITES.items():

            # If this building has multiple sprite states (normal, selected, etc.)
            if isinstance(sprite_info, dict):
                self.building_sprites[building_type] = {
                    key: pygame.image.load(os.path.join(self.building_path, filename)).convert_alpha()
                    for key, filename in sprite_info.items()
                }

            # Backwards compatibility: single-sprite buildings
            else:
                path = os.path.join(self.building_path, sprite_info)
                self.building_sprites[building_type] = pygame.image.load(path).convert_alpha()

    def load_building_icons(self):
        self.building_icons = {}
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
        self.resource_sprites = {}
        for res_type, filename in RESOURCE_SPRITES.items():
            full_path = os.path.join(RESOURCES_PATH, filename)
            self.resource_sprites[res_type] = pygame.image.load(full_path).convert_alpha()

    # loads the sprites for ui resource icons
    def load_resource_icons(self):
        self.resource_animations = {}

        for res_type, data in RESOURCE_ICONS.items():
            filename = data[0]
            full_path = os.path.join(RESOURCE_ICONS_PATH, filename)

            rows = data[3]
            cols = data[4]
            
            self.resource_animations[res_type] = AnimatedSprite(full_path, rows, cols)

    # Displays the resource icons in the top right corner of the screen, with animation.
    def display_resource_icons(self, res_type):
        anim = self.resource_animations.get(res_type)
        if not anim: return
        
        w, h = self.screen.get_size()
        sprite = anim.get_current_frame()

        icon_positions = {
            "food": w * 0.11,
            "wood": w * 0.34,
            "gold": w * 0.64,
            "population": w * 0.87
        }

        res_x = icon_positions.get(res_type, 0)
        res_y = 2
        
        rect = sprite.get_rect(topright=(res_x, res_y))
        self.screen.blit(sprite, rect)

    # Loads the sprites for the UI elements
    def load_ui_elements(self):
            self.ui_elements = {}
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

    # Displays the resource bar at the top of the screen
    def display_resource_bar(self):
        bar_sprite = self.ui_elements.get("resource_bar")
        w, h = self.screen.get_size() # Get live width

        if bar_sprite:
            # 3 slice
            edge_width = 50 
            
            # Left Cap
            self.screen.blit(bar_sprite, (0, 0), (0, 0, edge_width, bar_sprite.get_height()))
            
            # Middle (Stretched)
            middle_section = bar_sprite.subsurface((edge_width, 0, bar_sprite.get_width() - (edge_width * 2), bar_sprite.get_height()))
            stretched_middle = pygame.transform.scale(middle_section, (w - (edge_width * 2), bar_sprite.get_height()))
            self.screen.blit(stretched_middle, (edge_width, 0))
            
            # Right Cap
            self.screen.blit(bar_sprite, (w - edge_width, 0), (bar_sprite.get_width() - edge_width, 0, edge_width, bar_sprite.get_height()))

        text_color = (255, 255, 255)
        font = pygame.font.SysFont(None, 60)

        # Population
        self.population = len(self.units)
        max_pop = 0
        for building in self.buildings:
            if building.is_constructed:
                max_pop += building.population_limit

        food_text = f" {self.food_amount}"
        wood_text = f" {self.wood_amount}"
        gold_text = f" {self.gold_amount}"
        pop_text = f" {self.population} / {max_pop}"

        f_surface = font.render(food_text, True, text_color)
        w_surface = font.render(wood_text, True, text_color)
        g_surface = font.render(gold_text, True, text_color)
        p_surface = font.render(pop_text, True, text_color)

        # dynamic text positions.
        f_x = w * 0.12  # Food at ~12%
        w_x = w * 0.35  # Wood at ~35%
        g_x = w * 0.65  # Gold at ~65%
        p_x = w * 0.88  # Pop at ~88%

        f_y = (58 - f_surface.get_height())
        w_y = (58 - w_surface.get_height())
        g_y = (58 - g_surface.get_height())
        p_y = (58 - p_surface.get_height())

        self.screen.blit(f_surface, (f_x, f_y))
        self.screen.blit(w_surface, (w_x, w_y))
        self.screen.blit(g_surface, (g_x, g_y))
        self.screen.blit(p_surface, (p_x, p_y))

    # 'Cinematic' effect of following enemy units during enemy turn.
    def follow_enemy_camera(self, enemy):
        draw_x, draw_y = self.draw_coords(enemy.x, enemy.y)
        screen_x, screen_y = self.screen_coords(draw_x, draw_y)

        if screen_x < MARGIN:
            self.camera_x += SCROLL_SPEED
        elif screen_x > SCREEN_WIDTH - MARGIN:
            self.camera_x -= SCROLL_SPEED
        if screen_y < MARGIN:
            self.camera_y += SCROLL_SPEED
        elif screen_y > SCREEN_HEIGHT - MARGIN:
            self.camera_y -= SCROLL_SPEED

    # Camera follows hovered tile
    def display_hovered_tile(self):
        # The hovered tile is selected
        self.hovered_tile = self.selected_tile

        # Convert hovered tile to screen coordinates
        draw_x, draw_y = self.draw_coords(self.hovered_tile[0], self.hovered_tile[1])
        screen_x, screen_y = self.screen_coords(draw_x, draw_y)

        # Camera follow
        if screen_x < MARGIN:
            self.camera_x += SCROLL_SPEED
        elif screen_x > SCREEN_WIDTH - MARGIN:
            self.camera_x -= SCROLL_SPEED

        if screen_y < MARGIN:
            self.camera_y += SCROLL_SPEED
        elif screen_y > SCREEN_HEIGHT - MARGIN:
            self.camera_y -= SCROLL_SPEED

        # If a unit is selected, make it look at the hovered tile
        if self.selected_unit_id is not None and not self.selected_unit.unit_tired():
            # Find the actual unit object
            unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
            if unit:
                # Update direction: compare unit's position to where the "cursor" is
                unit.update_direction(unit.x, unit.y, self.hovered_tile[0], self.hovered_tile[1])

    # Centers the camera back onto the selected_tile.
    def camera_lerp(self):
        # 1. Calculate the destination coordinates
        draw_x, draw_y = self.draw_coords(self.selected_tile[0], self.selected_tile[1])
        world_x, world_y = self.screen_coords(draw_x, draw_y)
        
        target_x = (SCREEN_WIDTH // 2) - world_x
        target_y = (SCREEN_HEIGHT // 2) - world_y

        # 2. Lerp towards destination
        lerp_speed = 0.1 
        self.camera_x += (target_x - self.camera_x) * lerp_speed
        self.camera_y += (target_y - self.camera_y) * lerp_speed

        # 3. Check if we are close enough to stop
        if abs(self.camera_x - target_x) < 1 and abs(self.camera_y - target_y) < 1:
            self.camera_x = target_x
            self.camera_y = target_y
            self.camera_return = False

    # Removes a resource from the map when the tile is built on
    def cover_resources(self, x, y):
        for resource in self.resources:
            if resource.x == x and resource.y == y:
                self.resources.remove(resource)
                
# === MAP DISPLAYING ===

    # Displays a circular mini map in the bottom right corner of the screen.
    def draw_tactical_map(self):
        # Mini map dimensions and position
        
        # Create a surface for the circular mini map with per-pixel alpha
        mini_map_surface = pygame.Surface((self.minimap_size, self.minimap_size), pygame.SRCALPHA)
        
        # Draw semi-transparent circular background - smaller circle
        # circle_radius = int(RADIUS * 0.85)
        pygame.draw.circle(mini_map_surface, (32, 32, 32, 200), (self.radius, self.radius), self.smaller_radius)
        
        # Calculate offset to center the map on the minimap center
        center_sum = (PLAYABLE_WIDTH + PLAYABLE_HEIGHT - 2) // 2
        offset_x = self.radius
        offset_y = self.radius - center_sum * self.mini_map_scale
        
        # Draw only visible tiles
        for x in range(PLAYABLE_WIDTH):
            for y in range(PLAYABLE_HEIGHT):
                vis = VISIBILITY_MAP[x][y]
                if vis == 0:
                    continue  # Skip tiles not visible
                tile = PLAYABLE_MAP[x][y]
                color = TILE_DRAW_COLORS.get(tile, (255, 0, 255))

                draw_x = int((x - y) * self.mini_map_scale + offset_x)
                draw_y = int((x + y) * self.mini_map_scale + offset_y)
                
                # Check if point is within circle before drawing
                dist_from_center = ((draw_x - self.radius) ** 2 + (draw_y - self.radius) ** 2) ** 0.5
                if dist_from_center < self.smaller_radius:
                    # Top-down diamond tile
                    pygame.draw.polygon(mini_map_surface, color, [
                        (draw_x, draw_y - self.mini_map_scale),
                        (draw_x + self.mini_map_scale, draw_y),
                        (draw_x, draw_y + self.mini_map_scale),
                        (draw_x - self.mini_map_scale, draw_y)
                    ])

        # Only draw player units/buildings/resources if on visible tiles
        for unit in self.units:
            ux, uy = int(unit.x), int(unit.y)
            if 0 <= ux < PLAYABLE_WIDTH and 0 <= uy < PLAYABLE_HEIGHT and VISIBILITY_MAP[ux][uy] != 0:
                draw_x = int((ux - uy) * self.mini_map_scale + offset_x)
                draw_y = int((ux + uy) * self.mini_map_scale + offset_y)
                dist_from_center = ((draw_x - self.radius) ** 2 + (draw_y - self.radius) ** 2) ** 0.5
                if dist_from_center < self.smaller_radius:
                    self.draw_unit(ux, uy, mini_map_surface, draw_x, draw_y)
        
        for building in self.buildings:
            bx, by = int(building.x), int(building.y)
            if 0 <= bx < PLAYABLE_WIDTH and 0 <= by < PLAYABLE_HEIGHT and VISIBILITY_MAP[bx][by] != 0:
                draw_x = int((bx - by) * self.mini_map_scale + offset_x)
                draw_y = int((bx + by) * self.mini_map_scale + offset_y)
                dist_from_center = ((draw_x - self.radius) ** 2 + (draw_y - self.radius) ** 2) ** 0.5
                if dist_from_center < self.smaller_radius:
                    self.draw_building(bx, by, mini_map_surface, draw_x, draw_y)
        
        for res in self.resources:
            rx, ry = int(res.x), int(res.y)
            if 0 <= rx < PLAYABLE_WIDTH and 0 <= ry < PLAYABLE_HEIGHT and VISIBILITY_MAP[rx][ry] != 0:
                draw_x = int((rx - ry) * self.mini_map_scale + offset_x)
                draw_y = int((rx + ry) * self.mini_map_scale + offset_y)
                dist_from_center = ((draw_x - self.radius) ** 2 + (draw_y - self.radius) ** 2) ** 0.5
                if dist_from_center < self.smaller_radius:
                    self.draw_resource(rx, ry, mini_map_surface, draw_x, draw_y)
        
        self.map_outline(mini_map_surface, offset_x, offset_y)
        
        # Blit the mini map surface to the screen
        self.screen.blit(mini_map_surface, (self.mini_map_center_x - self.radius, self.mini_map_center_y - self.radius))
        
        # Draw circular border
        pygame.draw.circle(self.screen, (205, 195, 183), (self.mini_map_center_x, self.mini_map_center_y), self.smaller_radius, 5)

    def map_outline(self, surface, offset_x, offset_y):
        # Draw yellow outline around playable map with margin
        margin = -1  # tile margin inward from edges
        corners = [
            (margin, margin),                           # top-left
            (PLAYABLE_WIDTH - 1 - margin, margin),      # top-right
            (PLAYABLE_WIDTH - 1 - margin, PLAYABLE_HEIGHT - 1 - margin),  # bottom-right
            (margin, PLAYABLE_HEIGHT - 1 - margin)      # bottom-left
        ]
        # Top-down diamond view (rotate 45 degrees without isometric compression)
        corners_screen = []
        for x, y in corners:
            draw_x = int((x - y) * self.mini_map_scale + offset_x)
            draw_y = int((x + y) * self.mini_map_scale + offset_y)
            corners_screen.append([draw_x, draw_y])
        # Draw diamond outline using polygon (unfilled, just the border)
        if len(corners_screen) >= 3:
            pygame.draw.polygon(surface, (255, 255, 0), corners_screen, 2)

    # Displays units on the map
    def draw_unit(self, x, y, surface=None, pre_calc_x=None, pre_calc_y=None):
        if surface is None:
            surface = self.screen
            if pre_calc_x is None or pre_calc_y is None:
                draw_x = (x - y) * HALF_WIDTH + OFFSET_DRAW_X + (PLAYABLE_WIDTH * HALF_WIDTH)
                draw_y = (x + y) * HALF_HEIGHT + OFFSET_DRAW_Y + (PLAYABLE_HEIGHT * HALF_HEIGHT) // 2
            else:
                draw_x = pre_calc_x
                draw_y = pre_calc_y
        else:
            # Using pre-calculated coordinates for minimap
            draw_x = pre_calc_x
            draw_y = pre_calc_y
        triangle_points = [
            (draw_x, draw_y - HALF_HEIGHT),
            (draw_x - HALF_WIDTH, draw_y + HALF_HEIGHT),
            (draw_x + HALF_WIDTH, draw_y + HALF_HEIGHT),
        ]
        pygame.draw.polygon(surface, (255, 255, 255), triangle_points)

    # Displays buildings on the map
    def draw_building(self, x, y, surface=None, pre_calc_x=None, pre_calc_y=None):
        if surface is None:
            surface = self.screen
            if pre_calc_x is None or pre_calc_y is None:
                draw_x = (x - y) * HALF_WIDTH + OFFSET_DRAW_X + (PLAYABLE_WIDTH * HALF_WIDTH)
                draw_y = (x + y) * HALF_HEIGHT + OFFSET_DRAW_Y + (PLAYABLE_HEIGHT * HALF_HEIGHT) // 2
            else:
                draw_x = pre_calc_x
                draw_y = pre_calc_y
        else:
            # Using pre-calculated coordinates for minimap
            draw_x = pre_calc_x
            draw_y = pre_calc_y
        size = HALF_WIDTH // 2
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))

    # Displays resources on the map
    def draw_resource(self, x, y, surface=None, pre_calc_x=None, pre_calc_y=None):
        if surface is None:
            surface = self.screen
        # Only draw resources if tile is visible
        if 0 <= x < PLAYABLE_WIDTH and 0 <= y < PLAYABLE_HEIGHT and VISIBILITY_MAP[x][y] == 2:
            if pre_calc_x is None or pre_calc_y is None:
                draw_x = (x - y) * HALF_WIDTH + OFFSET_DRAW_X + (PLAYABLE_WIDTH * HALF_WIDTH)
                draw_y = (x + y) * HALF_HEIGHT + OFFSET_DRAW_Y + (PLAYABLE_HEIGHT * HALF_HEIGHT) // 2
            else:
                draw_x = pre_calc_x
                draw_y = pre_calc_y
            circle_radius = HALF_WIDTH // 2
            pygame.draw.circle(surface, (255, 255, 255), (draw_x, draw_y), circle_radius)

    # Displays highlighted reachable tiles
    def draw_tile_highlight(self, tx, ty, color, alpha=128):
        draw_tx, draw_ty = self.draw_coords(tx, ty)
        screen_x, screen_y = self.screen_coords(draw_tx, draw_ty)

        overlay = pygame.Surface((BASE_TILE_WIDTH, BASE_TILE_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(overlay, color, [
            (BASE_TILE_WIDTH // 2, 0),
            (BASE_TILE_WIDTH, BASE_TILE_HEIGHT // 2),
            (BASE_TILE_WIDTH // 2, BASE_TILE_HEIGHT),
            (0, BASE_TILE_HEIGHT // 2)
        ])
        self.screen.blit(overlay, (screen_x - BASE_TILE_WIDTH // 2, screen_y))

    # Displays the red hovered tile
    def draw_tile_highlight_crimson(self, tx, ty, color=(220, 20, 60)):
        draw_tx, draw_ty = self.draw_coords(tx, ty)
        screen_x, screen_y = self.screen_coords(draw_tx, draw_ty)

        # Define the diamond shape points
        points = [
            (screen_x, screen_y),  # top
            (screen_x + BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),  # right
            (screen_x, screen_y + BASE_TILE_HEIGHT),  # bottom
            (screen_x - BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),  # left
        ]

        # Draw the outline, not a filled polygon
        pygame.draw.polygon(self.screen, color, points, width=5)

# === UNIT ACTIONS ===

    # Displays a popup menu of the units available actions
    def display_unit_actions(self):

        options = ["Move", "Undo Move"]
        actions = {
            "Move": self.move_action,
            "Undo Move": self.undo_move
        }

        landed_tile = (int(self.selected_unit.x), int(self.selected_unit.y))

        # If the unit is a villager, allow building if tile is empty
        if self.selected_unit.type == "Villager":
            if not self.is_tile_occupied(*self.hovered_tile):
                options.insert(1, "Build")
                actions["Build"] = self.build_action
                for res in self.resources:
                    if (res.x, res.y) == landed_tile:
                        options.insert(2, "Gather")
                        actions["Gather"] = lambda u=self.selected_unit, r=res: self.gather_action(u, r)
                        break
            else:
                for res in self.resources:
                    if (res.x, res.y) == landed_tile:
                        options.insert(1, "Gather")
                        actions["Gather"] = lambda u=self.selected_unit, r=res: self.gather_action(u, r)
                        break

        # Ranged attack logic
        if self.selected_unit.attack_range > 1:
            # Get all potential targets
            potential_enemies = self.target_aquisition.all_ranged_enemies(
                self.selected_tile, self.selected_unit.attack_range, self.enemy_units
            )
            potential_buildings = self.target_aquisition.all_ranged_buildings(
                self.selected_tile, self.selected_unit.attack_range, self.e_buildings, self.enemy_units
            )

            # Filter: Is at least one enemy unit visible?
            visible_enemy_exists = any(
                VISIBILITY_MAP[int(e.x)][int(e.y)] == 2 for e in potential_enemies
            )
            # Filter: Is at least one building visible? 
            visible_building_exists = any(
                VISIBILITY_MAP[int(b.x)][int(b.y)] == 2 for b in potential_buildings
            )

            if visible_enemy_exists or visible_building_exists:
                options.insert(0, "Attack")
                actions["Attack"] = lambda: self.attack_action(self.selected_unit)

        # Melee attack logic
        else:
            adj_enemies = self.target_aquisition.all_adjacent_enemies(self.selected_tile, self.enemy_units)
            adj_buildings = self.target_aquisition.all_adjacent_buildings(self.selected_tile, self.e_buildings, self.enemy_units)

            visible_enemy_exists = any(
                VISIBILITY_MAP[int(e.x)][int(e.y)] == 2 for e in adj_enemies
            )
            visible_building_exists = any(
                VISIBILITY_MAP[int(b.x)][int(b.y)] == 2 for b in adj_buildings
            )

            if visible_enemy_exists or visible_building_exists:
                options.insert(0, "Attack")
                actions["Attack"] = lambda: self.attack_action(self.selected_unit)

        self.popup_menu.open(options, actions)

    # Moves a unit and increases the action count by 1, deselects the unit, then closes the popup menu
    def move_action(self):
        self.reachable_tiles = set()
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit:
            selected_unit.rest()
            selected_unit.selected = False
        if not selected_unit.path: 
            selected_unit.update_vision_coords() # Sync coordinates
            self.update_VISIBILITY_MAP() # Refresh the Fog of War

        self.selected_unit_id = None
        self.popup_menu.close()
        self.message_box.close()

    # Returns the unit back to its original location
    def undo_move(self):
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit and selected_unit.previous_position:
            selected_unit.x, selected_unit.y = selected_unit.previous_position
        self.reachable_tiles = set()
        if selected_unit:
            selected_unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()

    # Displays a popup menu of the different buildings to construct and then calls the building selector
    def build_action(self):
        self.reachable_tiles = set()

        options = ["Town Centre", "House", "Market", "Mill"]
        actions = {
            "Town Centre": lambda: self.building_construction("town_centre"),
            "House": lambda: self.building_construction("house"),
            "Market": lambda: self.building_construction("market"),
            "Mill": lambda: self.building_construction("mill")
        }

        if self.is_adjacent_to_mill():
            options.append("Farm")
            actions["Farm"] = lambda: self.building_construction("farm")

        options.append("Cancel")
        actions["Cancel"] = self.cancel_action
        
        # Map icons to display names
        icon_mapping = {
            "Town Centre": self.building_icons.get("town_centre"),
            "House": self.building_icons.get("house"),
            "Market": self.building_icons.get("market"),
            "Mill": self.building_icons.get("mill"),
            "Farm": self.building_icons.get("farm"),
            "Cancel": None
        }

        # Store icons in a dedicated 'building_icons' key
        self.building_menu.sprites["building_icons"] = icon_mapping
        
        # Keep this as 'building_menu' so it still finds your hexagons!
        self.building_menu.sprite_key = "building_menu" 

        self.popup_menu.close()
        self.building_menu.open(options, actions)
    
    # Creates instance of chosen building and subtracts resource cost.
    def building_construction(self, building_name):
        # Aquiring list of building attributes
        if building_name in BUILDINGS:
            b_attr = BUILDINGS[building_name]
        elif building_name in RESOURCE_BUILDINGS:
            b_attr = RESOURCE_BUILDINGS[building_name]
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        # If player's resources are enough, subtract cost, and create building instance, append to 
        # building list.
        if self.food_amount >= b_attr[1] and self.wood_amount >= b_attr[2] and self.gold_amount >= b_attr[3]:
            self.cover_resources(selected_unit.x, selected_unit.y)
            new_building_id = max([b.id for b in self.buildings], default=0) + 1
            new_building = BaseBuildings(self.selected_tile[0], self.selected_tile[1], b_attr[4], b_attr[5])
            new_building.id = new_building_id
            new_building.type = building_name
            new_building.building_queued()
            new_building.is_constructed = False
            self.buildings.append(new_building)
            if building_name in RESOURCE_BUILDINGS:
                new_resource = ResourceSource(self.selected_tile[0], self.selected_tile[1], b_attr[6], b_attr[7], True)
                self.resources.append(new_resource)
            self.popup_menu.close()
            self.building_menu.close()
            if selected_unit:
                selected_unit.rest()
                self.construction[selected_unit] = new_building
                selected_unit.selected = False
            if not selected_unit.path: 
                selected_unit.update_vision_coords() # Sync coordinates
                self.update_VISIBILITY_MAP() # Refresh the Fog of War
            # Subtracts resource cost
            self.food_amount -= b_attr[1]
            self.wood_amount -= b_attr[2]
            self.gold_amount -= b_attr[3]
            self.selected_unit_id = None
        else:
            self.message_box.open("Insufficient funds", self.error_message)
            # self.cancel_action()

    # Returns to the previous popup menu
    def cancel_action(self):
        self.building_menu.close()
        self.popup_menu.is_open = True

    # Unit gathers the resource from the resource tile its on and increases the action count by 1
    def gather_action(self, unit, resource):
        self.reachable_tiles = set()
        unit.is_gathering = True
        unit.gather_resource_id = resource.id
        if unit:
            unit.rest()
            unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()

    # Unit enters target aquisition mode
    def attack_action(self, unit):
        # Find all enemy units and buildings in range
        if unit.attack_range > 1:
            enemies = self.target_aquisition.all_ranged_enemies(
                self.selected_tile, unit.attack_range, self.enemy_units)
            enemy_buildings = self.target_aquisition.all_ranged_buildings(
                self.selected_tile, unit.attack_range, self.e_buildings, self.enemy_units)
        # Find all adjacent enemy units and buildings
        else:
            enemies = self.target_aquisition.all_adjacent_enemies(self.selected_tile, self.enemy_units)
            enemy_buildings = self.target_aquisition.all_adjacent_buildings(
                self.selected_tile, self.e_buildings, self.enemy_units)
                
        targets = []
        for e in enemies:
            targets.append(('unit', e))
        for b in enemy_buildings:
            if not self.target_aquisition.is_unit_on_building(b, self.enemy_units):
                targets.append(('building', b))

        # Always enter targeting mode, even for single target
        self.reachable_tiles = set()
        self.popup_menu.close()

        self.target_select_mode = True
        self.targetable_enemies = targets
        self.selected_target_index = 0
        kind, target = self.targetable_enemies[self.selected_target_index]
        self.selected_tile = (int(target.x), int(target.y))
        self.hovered_tile = self.selected_tile

    # Unit enters attack confirmation/target selection if there are multiple targets. Shift on hovered
    # tile to select an enemy unit.
    def open_attack_confirm_menu(self):
        # Called after target selection (even if only one target)
        options = ["Attack", "Undo Move"]
        actions = {
            "Attack": self.execute_attack,
            "Undo Move": self.undo_attack
        }
        self.popup_menu.open(options, actions)

    # Executes the players attack and calculates resulting damage. Also runs enemy retaliation
    def execute_attack(self):
        # Actually execute the attack on the selected target
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        kind, target = self.targetable_enemies[self.selected_target_index]

        # kind: 'unit' or 'building'
        if kind == 'unit':
            enemy = target
            damage = ((selected_unit.attack * (1 + BONUS_MULTIPLYER))/enemy.defense) * 25 + FLAT_BONUS
            enemy.health -= damage
            dist = abs(selected_unit.x - enemy.x) + abs(selected_unit.y - enemy.y)
            self.retaliate_attack(selected_unit, enemy, dist)
            print("enemy:", enemy.health)
            print("player:", selected_unit.health)
        elif kind == 'building':
            building = target
            damage = ((selected_unit.attack * (1 + BONUS_MULTIPLYER))/max(1, getattr(building, "defense", 1))) * 25 + FLAT_BONUS
            building.hitpoints -= damage
            print("building:", building.hitpoints)
        selected_unit.rest()
        self.reachable_tiles = set()

        if not selected_unit.path: 
            selected_unit.update_vision_coords() # Sync coordinates
            self.update_VISIBILITY_MAP() # Refresh the Fog of War

        if selected_unit:
            selected_unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()
        self.target_select_mode = False
        self.targetable_enemies = []
        self.selected_target_index = 0

    # Same as undo_move, but also close target select mode
    def undo_attack(self):
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit and hasattr(selected_unit, "previous_position"):
            selected_unit.x, selected_unit.y = selected_unit.previous_position
        self.reachable_tiles = set()
        if selected_unit:
            selected_unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()
        self.target_select_mode = False
        self.targetable_enemies = []
        self.selected_target_index = 0

# === BUILDING ACTIONS ===

    # Displays a popup menu of the selected building's actions such as training or researching.
    def building_actions(self, building):
        if not building.building_tired():
            building.selected = True
            building_name = building.type
            if building_name in BUILDINGS:
                building_actions = ["Train", "Research", "Cancel"]
                building_callbacks = {
                    "Train": self.unit_selection,
                    "Research": self.research_action,
                    "Cancel": self.deselect
                }
            else:
                building_actions = ["Research", "Cancel"]
                building_callbacks = {
                    "Research": self.research_action,
                    "Cancel": self.deselect
                }
            self.popup_menu.open(building_actions, building_callbacks)

    # Displays a popup menu of the trainable units at the selected building, and spawns the unit
    def unit_selection(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        spawn_x, spawn_y = selected_building.x, selected_building.y
        building_name = selected_building.type
        # Finds the building's attribute list consisting of type, cost, and trainable units
        if building_name in BUILDINGS:
            b_attr = BUILDINGS[building_name]
        trainable_units = b_attr[6]

        # Collect all affordable units
        affordable_units = []
        for unit_name in trainable_units:
            # Aquires unit attribute list
            u_attr = UNITS[unit_name]
            food, wood, gold = u_attr[1], u_attr[2], u_attr[3]
            if (self.food_amount >= food and
                self.wood_amount >= wood and
                self.gold_amount >= gold):
                affordable_units.append(unit_name)

        # Displaying the affordable units in a popup menu
        options = affordable_units + ["Cancel"]
        actions = {
            unit: (lambda u=unit: self.train_action(u, spawn_x, spawn_y))
            for unit in trainable_units
        }
        actions["Cancel"] = lambda: self.building_actions(selected_building)

        self.popup_menu.open(options, actions)

    # Creates an instance of a unit with appropriate attributes.
    def train_action(self, unit_name, spawn_x, spawn_y):
        # Finds the unit's attribute list consisting of type, cost, movement, and defense values
        u_attr = UNITS[unit_name]
        # Creates a unit instance with appropriate attributes. Then subtracts from the player's 
        # resources based on its cost.
        new_unit = BaseUnits(spawn_x, spawn_y, u_attr[5], u_attr[6], u_attr[7], u_attr[8], type=unit_name)
        # Sets the unit's action count to 2 and appends it to the player's unit list.
        new_unit.unit_queued()
        self.units.append(new_unit)
        self.food_amount -= u_attr[1]
        self.wood_amount -= u_attr[2]
        self.gold_amount -= u_attr[3]
        # Sets the building's action count to 2
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        if selected_building:
            selected_building.rest()
            selected_building.rest()
            selected_building.selected = False
            self.selected_building_id = None
        self.popup_menu.close()
        self.message_box.close()

    # Research in buildings. Needs fixing
    def research_action(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        building_name = selected_building.type
        
        if building_name in BUILDINGS:
            tech_list = BUILDINGS[building_name][8]
        else:
            tech_list = RESOURCE_BUILDINGS[building_name][9]
        
        affordable_tech_keys = []
        options = []
        
        for r_key in tech_list:
            r_attr = RESEARCH[r_key]
            if (self.food_amount >= r_attr[1] and 
                self.wood_amount >= r_attr[2] and 
                self.gold_amount >= r_attr[3]):
                
                if r_key not in self.researched_techs and r_key not in self.pending_techs:
                    friendly_name = r_attr[0]
                    affordable_tech_keys.append(r_key)
                    options.append(friendly_name)

        actions = {}
        for i in range(len(affordable_tech_keys)):
            r_key = affordable_tech_keys[i]
            display_name = options[i]
            actions[display_name] = (lambda r=r_key: self.queue_research(r, selected_building))
            
        options.append("Cancel")
        actions["Cancel"] = lambda: self.building_actions(selected_building)

        self.popup_menu.open(options, actions)
    
    # Adds purchased research techs to a queue
    def queue_research(self, tech_key, building):
        r_attr = RESEARCH[tech_key]
        self.food_amount -= r_attr[1]
        self.wood_amount -= r_attr[2]
        self.gold_amount -= r_attr[3]

        self.pending_techs.append(tech_key)
        
        # Mark building as used so they can't research twice in one turn
        building.rest()
        building.selected = False
        building.selected_building_id = None
        self.popup_menu.close()
        self.message_box.close()

    # Activates tech researched from buildings.
    def complete_research(self, tech_key): 
        if tech_key not in self.researched_techs:
            self.researched_techs.add(tech_key)
            
            # Apply the effect immediately
            effect_key = RESEARCH[tech_key][5]
            effect_val = RESEARCH[tech_key][6]
            
            if "rate" in effect_key:
                self.tech_multipliers[effect_key] *= effect_val
            else:
                self.tech_multipliers[effect_key] += effect_val

            if "vision" in effect_key:
                self.update_VISIBILITY_MAP()

# === RESOURCE GATHERING ===

    # Processes player's resource gathering at the end of enemy turn
    def process_automatic_gathering(self):
        # Iterates over all units and checks if they are gathering. 
        for unit in self.units:
            if unit.is_gathering:
                res_id = unit.gather_resource_id
                res = next((r for r in self.resources if r.id == res_id), None)
                unit_tile = (int(unit.x), int(unit.y))
                
                if res and (res.x, res.y) == unit_tile:
                    # Determine base amount to take from the resource tile
                    raw_amount = min(100, res.amount)
                    res.amount -= raw_amount
                    
                    # Apply the specific multiplier based on resource type
                    if res.resource_type == "food":
                        multiplier = self.tech_multipliers.get("gather_rate_food", 1.0)
                        self.food_amount += int(raw_amount * multiplier)
                        
                    elif res.resource_type == "wood":
                        multiplier = self.tech_multipliers.get("gather_rate_wood", 1.0)
                        self.wood_amount += int(raw_amount * multiplier)
                        
                    elif res.resource_type == "gold":
                        multiplier = self.tech_multipliers.get("gather_rate_gold", 1.0)
                        self.gold_amount += int(raw_amount * multiplier)

                    # Handle depletion
                    if res.amount <= 0:
                        self.resources.remove(res)
                        self.message_box.open(f"{res.resource_type} has been depleted.", self.error_message)
                        unit.is_gathering = False
                        unit.gather_resource_id = None

    # Processed enemy's resource gathering at the end of enemy turn
    def process_enemy_gathering(self):
        # Iterates over all enemy units and checks if they are gathering. 
        for unit in self.enemy_units:
            if unit.is_gathering:
                res_id = unit.gather_resource_id
                # Iterates over resources and checks if their ID matches the one the unit is gathering
                # from. If the unit is gathering from a resource tile its on, it processes the gathering,
                # and if the resource has been depleted, it is deleted.
                res = next((r for r in self.resources if r.id == res_id), None)
                unit_tile = (int(unit.x), int(unit.y))
                if res and (res.x, res.y) == unit_tile:
                    amount_gathered = min(100, res.amount)
                    res.amount -= amount_gathered
                    if res.resource_type == "food":
                        self.enemy_food += amount_gathered
                    elif res.resource_type == "wood":
                        self.enemy_wood += amount_gathered
                    elif res.resource_type == "gold":
                        self.enemy_gold += amount_gathered
                    if res.amount <= 0:
                        self.resources.remove(res)
                        self.message_box.open(f"{res.resource_type} has been depleted.")
                        unit.is_gathering = False
                        unit.gather_resource_id = None
                
                print("food:", self.enemy_food, "wood:", self.enemy_wood, "gold:", self.enemy_gold)

# === TURN HANDLING === 

    # At the end of player's turn, resets unit and building action count
    def end_day(self):
        # Ends player turn
        self.player_turn = False
        # Iterates through all units and resets their action count.
        for unit in self.units:
            unit.rested()
        # Iterates through all buildings and resets their action count if they aren't under construction
        for building in self.buildings:
            if building.queued == False:
                building.rested()
        # Closes the popup menu
        self.popup_menu.close()

    # At the end of enemy's turn, resets enemy unit and building action count. Processes player
    # and enemy resource gathering, and trains enemy units.
    def end_enemy_day(self):
        # Starts the player turn. Processes unit and enemy resource gathering for the turn. Enemy Trains
        # their units
        self.player_turn = True

        if self.pending_techs:
            for tech in self.pending_techs:
                self.complete_research(tech)
            self.pending_techs.clear() # Clear queue after applying

        self.enemy_paths_planned = False
        self.process_automatic_gathering()
        self.process_enemy_gathering()
        self.enemy_ai.train_enemy_units(self.e_buildings, self.enemy_units, self)
        # Iterates through all player buildings and checks which ones are under construction. Completes
        # the buildings that are under construction and resets their action count.
        for building in self.buildings:
            if building.queued == True:
                for key, value in list(self.construction.items()):
                    print(self.construction)
                    building.is_constructed = True
                    building.queued == False
                    building.rested()
                    if value == building:
                        self.construction.pop(key)
                    print(self.construction)

    # Checks if conditions to end the game are True
    def check_game_over(self):
        # If there are no player units or buildings end the game
        if len(self.units) == 0 and len(self.buildings) == 0:
            self.game_state_manager.set_state("game over")
            return True
        # If there are no enemy units of buildings end the game
        elif len(self.enemy_units) == 0 and len(self.e_buildings) == 0:
            self.game_state_manager.set_state("game over")
            return True
        # Game continues running
        else:
            return False
        
# === EVENT HANDLING ===

    # Target selection
    def cycle_target(self):
        self.selected_target_index = (self.selected_target_index + 1) % len(self.targetable_enemies)
        kind, target = self.targetable_enemies[self.selected_target_index]
        self.selected_tile = (int(target.x), int(target.y))
        self.hovered_tile = self.selected_tile

    # Deselect unit/building, close menus
    def deselect(self):
        if self.selected_unit:
            self.selected_unit.selected = False
        if self.selected_building:
            self.selected_building.selected = False
        self.selected_unit = None
        self.selected_unit_id = None
        self.selected_building = None
        self.selected_building_id = None
        self.popup_menu.close()
        self.message_box.close()

    # Cycle through available player units
    def cycle_player_units(self):
        # Filter only non-tired units
        available_units = [u for u in self.units if not u.unit_tired()]

        if not available_units:
            # No units available to select
            return
        if self.selected_unit_id is not None:
            # Find current selected unit in the filtered list
            try:
                current_index = next(i for i, u in enumerate(available_units)
                                    if u.id == self.selected_unit_id)
                next_index = (current_index + 1) % len(available_units)
            except StopIteration:
                # Previously selected unit is now tired or missing
                next_index = 0
        else:
            next_index = 0
        # Deselect previous unit
        for u in self.units:
            u.selected = False

        # Select new unit
        self.selected_unit = available_units[next_index]
        self.selected_unit.selected = True
        self.selected_unit_id = self.selected_unit.id
        self.selected_tile = (int(self.selected_unit.x), int(self.selected_unit.y))

        # Pathfinding setup
        friendly_units_for_pathfinding = [u for u in self.units if u != self.selected_unit]
        path_finding = PathFinding(
            friendly_units_for_pathfinding,
            self.enemy_units,
            self.buildings,
            self.e_buildings,
            moving_side='player'
        )
        self.reachable_tiles = path_finding.bfs_reachable(
            (int(self.selected_unit.x), int(self.selected_unit.y)),
            self.selected_unit.movement_range
        )

        u_attr = UNITS[self.selected_unit.type]
        self.message_box.open(u_attr[9], False)
        
    # Unit selection
    def select_player_unit(self):
        # Attempts to select a player unit on the hovered tile. 
        for unit in self.units:
            if int(unit.x) == self.hovered_tile[0] and int(unit.y) == self.hovered_tile[1]:

                # Deselect previously selected unit
                if self.selected_unit_id is not None:
                    prev_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                    if prev_unit:
                        prev_unit.selected = False

                # Select new unit
                self.selected_unit = unit
                self.selected_unit_id = unit.id

                u_attr = UNITS[self.selected_unit.type]

                # Only show reachable tiles if unit is not tired
                if not self.selected_unit.unit_tired():
                    self.selected_unit.selected = True
                    self.selected_tile = (int(self.selected_unit.x), int(self.selected_unit.y))

                    friendly_units_for_pathfinding = [u for u in self.units if u != self.selected_unit]

                    path_finding = PathFinding(
                        friendly_units_for_pathfinding,   # player_units
                        self.enemy_units,                 # enemy_units
                        self.buildings,                   # player_buildings
                        self.e_buildings,                 # enemy_buildings
                        moving_side='player'
                    )

                    self.reachable_tiles = path_finding.bfs_reachable(
                        (int(unit.x), int(unit.y)),
                        unit.movement_range
                    )

                    # Deselect any selected building
                    if self.selected_building_id is not None:
                        prev_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
                        if prev_building:
                            prev_building.selected = False
                    self.selected_building_id = None

                self.message_box.open(u_attr[9], False)

                # Unit was found and processed
                return True
        # No unit found on hovered tile
        return False

    # Building selection
    def select_player_building(self):
        # Attempts to select a player building on the hovered tile
        for building in self.buildings:
            if int(building.x) == self.hovered_tile[0] and int(building.y) == self.hovered_tile[1]:

                # Deselect previously selected building
                if self.selected_building_id is not None:
                    prev_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
                    if prev_building:
                        prev_building.selected = False

                # Select new building
                self.selected_building = building
                self.selected_building_id = building.id

                if self.selected_building.type in BUILDINGS:
                    b_attr = BUILDINGS[self.selected_building.type]
                    b_desc = b_attr[7]
                elif self.selected_building.type in RESOURCE_BUILDINGS:
                    b_attr = RESOURCE_BUILDINGS[self.selected_building.type]
                    b_desc = b_attr[8]

                # Deselect any selected unit
                if self.selected_unit_id is not None:
                    prev_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                    if prev_unit:
                        prev_unit.selected = False
                    self.selected_unit_id = None
                    self.selected_unit = None
                    self.reachable_tiles = []

                # Trigger building actions popup
                self.building_actions(self.selected_building)

                self.message_box.open(b_desc, False)

                # Building found and processed
                return True
        # No building found on hovered tile  
        return False

    # Empty tile selection
    def select_empty_tile(self):
        
        # Deselect selected unit
        if self.selected_unit_id is not None:
            prev_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
            if prev_unit:
                prev_unit.selected = False
            self.selected_unit_id = None
            self.selected_unit = None
            self.reachable_tiles = []

        # Deselect selected building
        if self.selected_building_id is not None:
            prev_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
            if prev_building:
                prev_building.selected = False
            self.selected_building_id = None

        self.message_box.close()

        self.popup_menu.open(["End Day", "Cancel", "Quit"], 
                             {"End Day": self.end_day,
                              "Cancel": self.popup_menu.close,
                              "Quit": self.quit
                            }
        )

    # Unit movement
    def mobile_unit(self):
        # Find the unit object by its ID
        self.selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if self.selected_unit:
            # New PathFinding instance for this unit
            friendly_units_for_pathfinding = [u for u in self.units if u != self.selected_unit]
            path_finding = PathFinding(
                friendly_units_for_pathfinding,   # player_units
                self.enemy_units,                 # enemy_units
                self.buildings,                   # player_buildings
                self.e_buildings,                 # enemy_buildings
                moving_side='player'
            )
            self.tactical_map_mode = False
            if self.selected_tile in self.reachable_tiles:
                self.selected_unit.previous_position = (self.selected_unit.x, self.selected_unit.y)
                start_pos = (int(self.selected_unit.x), int(self.selected_unit.y))
                if self.selected_tile == start_pos:
                    self.selected_unit.path = [(float(self.selected_unit.x), float(self.selected_unit.y))]
                    self.is_moving = True
                else:
                    path = path_finding.a_star(start_pos, self.selected_tile, self.selected_unit.movement_range)
                    if path:
                        self.selected_unit.path = [(float(x), float(y)) for x, y in path]
                        self.is_moving = True

        old_x, old_y = self.selected_unit.x, self.selected_unit.y
        unit_x, unit_y = self.selected_tile
        self.selected_unit.update_direction(old_x, old_y, unit_x, unit_y)

        # self.message_box.close()

    # Checks if unit is gathering at a resource tile. If a unit moves off, it stops gathering.
    def gathering_check(self):
        if self.selected_unit.is_gathering:
                res_id = self.selected_unit.gather_resource_id
                res = next((r for r in self.resources if r.id == res_id), None)
                if not res or (int(self.selected_unit.x), int(self.selected_unit.y)) != (res.x, res.y):
                    self.selected_unit.is_gathering = False
                    self.selected_unit.gather_resource_id = None

# === UNIT / BUILDING HEALTH ===

    # Checks health of units and removes dead ones
    def unit_health(self):
        for unit in self.units:
            if unit.health <= 0:
                print(f"Player at ({unit.x},{unit.y}) is defeated!")
                # Remove any dead units from construction dictionary.
                for key in list(self.construction):
                    if key == unit:
                        self.construction.pop(key)
                self.units.remove(unit)

    # Checks health of buildings and removes destroyed ones
    def building_health(self):
        for building in self.buildings:
            if building.hitpoints <= 0:
                print(f"Building at ({building.x},{building.y}) is destroyed!")
                self.buildings.remove(building)

    # Checks health of enemy units and removes dead ones
    def enemy_unit_health(self):
        for enemy in self.enemy_units:
            if enemy.health <= 0:
                self.enemy_units.remove(enemy)
                print(enemy, "died")

    # Checks health of enemy buildings and removes destroyed ones
    def enemy_building_health(self):
        for eb in self.e_buildings:
            if eb.hitpoints <= 0:
                print(f"Building at ({eb.x},{eb.y}) is destroyed!")
                self.e_buildings.remove(eb)

# === MISC. ===

    # Checks if the selected tile is adjacent to a mill for farm building   
    def is_adjacent_to_mill(self):
        tx, ty = self.selected_tile
        # Get all 8 neighbors (North, South, East, West, and diagonals)
        neighbors = [
            (tx-1, ty), (tx+1, ty), (tx, ty-1), (tx, ty+1),
            (tx-1, ty-1), (tx+1, ty-1), (tx-1, ty+1), (tx+1, ty+1)
        ]
        
        for b in self.buildings:
            # Check if building is a Mill and its position matches any neighbor
            if b.type == "mill" and (int(b.x), int(b.y)) in neighbors:
                return True
        return False

    # Quits the game.
    def quit(self):
        self.running = False

    # Iterates over all buildings to check if there is a building on the hovered tile
    def is_tile_occupied(self, x, y):
        return any(b.x == x and b.y == y for b in self.buildings)

    def retaliate_attack(self, attacker, defender, distance):
        defender_range = defender.attack_range
        # Melee retaliation: only if defender is melee and distance==1
        if defender_range == 1 and distance == 1:
            damage = ((defender.attack * (1 + BONUS_MULTIPLYER)) / attacker.defense) * 25 + FLAT_BONUS
            attacker.health -= damage
        # Ranged retaliation: only if not melee (distance > 1 and ≤ range)
        elif defender_range > 1 and 1 < distance < defender_range:
            damage = ((defender.attack * (1 + BONUS_MULTIPLYER)) / attacker.defense) * 25 + FLAT_BONUS
            attacker.health -= damage

    # Returns (draw_tx, draw_ty)
    def draw_coords(self, x, y):
        draw_tx = x + OFFSET_X
        draw_ty = y + OFFSET_Y

        return (draw_tx, draw_ty)
    
    def screen_coords(self, x, y):
        draw_x = x
        draw_y = y

        screen_x = ((draw_x - draw_y) * BASE_TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + self.camera_x)
        screen_y = ((draw_x + draw_y) * BASE_TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + self.camera_y)

        return(screen_x, screen_y)

    # Resize 
    def resize(self, w, h):
        self.screen = pygame.display.get_surface()

        # Mini-map Sizing
        self.minimap_size = int(h * 0.42) 
        self.radius = self.minimap_size // 2
        self.smaller_radius = int(self.radius * 0.85)
        
        # Recalculate scale so the map fills the new circle size
        self.mini_map_scale = int(self.radius // (PLAYABLE_WIDTH // 2 + 1) * 0.40)

        # Update Mini-map center (Bottom Right)
        self.mini_map_center_x = w - self.radius - 20 # 20px margin
        self.mini_map_center_y = h - self.radius - 20

        # Update the Message Box position
        self.message_box.update_position(w, h)

        # Update the Popup menu and Build menu position
        self.popup_menu.resize(w, h)
        self.building_menu.resize(w, h)

# === GAME LOOP ===

    def run(self, events):
        # global actions, callbacks
        if not self.game_over:
            # Events during the player's turn
            if self.player_turn:
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                        return

                    if event.type == pygame.KEYDOWN:
                        # Building menu
                        if self.building_menu.is_open:
                            if event.key in [pygame.K_w, pygame.K_UP]:
                                self.building_menu.move_selection(-1)
                            elif event.key in [pygame.K_s, pygame.K_DOWN]:
                                self.building_menu.move_selection(1)
                            elif event.key == pygame.K_LSHIFT:
                                self.building_menu.select()
                            continue

                        # Popup menu
                        if self.popup_menu.is_open:
                            if event.key in [pygame.K_w, pygame.K_UP]:
                                self.popup_menu.move_selection(-1)
                            elif event.key in [pygame.K_s, pygame.K_DOWN]:
                                self.popup_menu.move_selection(1)
                            elif event.key == pygame.K_LSHIFT:
                                self.popup_menu.select()
                            return # Block all other inputs

                        # Target selection
                        if self.target_select_mode:
                            if event.key == pygame.K_TAB and self.targetable_enemies:
                                self.cycle_target()
                            elif event.key == pygame.K_LSHIFT:
                                self.open_attack_confirm_menu()
                            elif event.key == pygame.K_ESCAPE:
                                self.target_select_mode = False
                                self.popup_menu.is_open = True
                            return
                        
                        # Deselect units or buildings
                        if event.key == pygame.K_ESCAPE:
                            self.deselect()
                            self.message_box.close()

                        # Cycles through available units
                        elif event.key == pygame.K_TAB:
                            self.cycle_player_units()

                        # Selection/Deselection and movement with shift key
                        elif event.key == pygame.K_LSHIFT:
                            # CASE 1: A unit is already selected and we are clicking an empty/different tile to move
                            if self.selected_unit_id is not None:
                                # Check if the hovered tile is within reachable range
                                if self.hovered_tile in self.reachable_tiles:
                                    self.selected_tile = self.hovered_tile # Set destination
                                    self.mobile_unit()
                                    # Return/Continue so we don't immediately re-select the unit we just moved
                                else:
                                    # If we clicked outside movement range, treat it as a deselection/re-selection attempt
                                    unit_found = self.select_player_unit()
                                    if not unit_found:
                                        building_found = self.select_player_building()
                                        if not building_found:
                                            self.select_empty_tile()
                                            self.message_box.close()

                            # CASE 2: No unit is currently selected
                            else:
                                unit_found = self.select_player_unit()
                                if not unit_found:
                                    building_found = self.select_player_building()
                                    if not building_found:
                                        self.select_empty_tile()
                                pass

                # Get the state of all keys (runs every frame for continuous movement)
                keys = pygame.key.get_pressed()

                # Only allow camera movement and tile movement if no popup menu is open
                if not self.popup_menu.is_open and not self.building_menu.is_open:

                    # Camera control
                    if keys[pygame.K_c]:
                        self.free_cam_active = True
                        self.camera_return = False

                        # Move camera directly instead of the tile
                        if keys[pygame.K_w] or keys[pygame.K_UP]:
                            self.camera_y += SCROLL_SPEED
                        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                            self.camera_y -= SCROLL_SPEED
                        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                            self.camera_x += SCROLL_SPEED
                        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                            self.camera_x -= SCROLL_SPEED
                    else:
                        # If we just let go of C, snap back
                        if self.free_cam_active:
                            self.camera_return = True
                            self.free_cam_active = False

                        # SMOOTH RETURN LOGIC
                        if self.camera_return:
                            self.camera_lerp()

                        # Decrement movement delay
                        if self.tile_move_delay > 0:
                            self.tile_move_delay -= 1

                        # Movement with WASD or arrow keys.
                        # Check each key (this will run every frame the key is held)
                        # Only move if delay counter is 0, and only allow ONE direction per cycle
                        if self.tile_move_delay == 0:
                            if keys[pygame.K_w] and self.selected_tile[1] > 0:
                                self.selected_tile = (self.selected_tile[0], self.selected_tile[1] - 1)
                                self.tile_move_delay = 10  # Adjust this value to control speed (higher = slower)
                            elif keys[pygame.K_s] and self.selected_tile[1] < PLAYABLE_HEIGHT - 1:
                                self.selected_tile = (self.selected_tile[0], self.selected_tile[1] + 1)
                                self.tile_move_delay = 10
                            elif keys[pygame.K_a] and self.selected_tile[0] > 0:
                                self.selected_tile = (self.selected_tile[0] - 1, self.selected_tile[1])
                                self.tile_move_delay = 10
                            elif keys[pygame.K_d] and self.selected_tile[0] < PLAYABLE_WIDTH - 1:
                                self.selected_tile = (self.selected_tile[0] + 1, self.selected_tile[1])
                                self.tile_move_delay = 10
                            elif keys[pygame.K_UP] and self.selected_tile[1] > 0:
                                self.selected_tile = (self.selected_tile[0], self.selected_tile[1] - 1)
                                self.tile_move_delay = 10  # Adjust this value to control speed (higher = slower)
                            elif keys[pygame.K_DOWN] and self.selected_tile[1] < PLAYABLE_HEIGHT - 1:
                                self.selected_tile = (self.selected_tile[0], self.selected_tile[1] + 1)
                                self.tile_move_delay = 10
                            elif keys[pygame.K_LEFT] and self.selected_tile[0] > 0:
                                self.selected_tile = (self.selected_tile[0] - 1, self.selected_tile[1])
                                self.tile_move_delay = 10
                            elif keys[pygame.K_RIGHT] and self.selected_tile[0] < PLAYABLE_WIDTH - 1:
                                self.selected_tile = (self.selected_tile[0] + 1, self.selected_tile[1])
                                self.tile_move_delay = 10
            
            # Enemy turn
            else: 
                if not self.enemy_paths_planned:
                    self.enemy_ai.plan_enemy_paths(self.enemy_units, self.units, self.buildings, self.resources)
                    self.enemy_paths_planned = True
                    self.enemy_turn_index = 0
                    self.enemy_turn_phase = 'move'
                    self.enemy_turn_delay = 0

                # If all enemies processed, the enemy turn ends
                if self.enemy_turn_index >= len(self.enemy_units):
                    self.end_enemy_day()
                    return

                enemy = self.enemy_units[self.enemy_turn_index]
                # Delay between actions for clarity/animation (e.g. 15 frames = 0.25s at 60 FPS)
                if self.enemy_turn_delay > 0:
                    self.enemy_turn_delay -= 1
                    return

                if self.enemy_turn_phase == 'move':
                    # Animate movement
                    if enemy.path:
                        enemy.move_along_path()
                        self.follow_enemy_camera(enemy)
                        # Only move one tile per frame or step (for clarity/animation)
                        self.enemy_turn_delay = 0  # Adjust as needed for game speed
                        if not enemy.path:
                            self.enemy_turn_phase = 'attack'
                    else:
                        self.enemy_turn_phase = 'attack'

                elif self.enemy_turn_phase == 'attack':
                    # Try to attack player unit/building
                    did_attack = False
                    # Player units take damage from enemy attacks
                    for player in self.units:
                        dist = abs(enemy.x - player.x) + abs(enemy.y - player.y)
                        if player.health > 0 and dist == 1:
                            damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/player.defense) * 25 + FLAT_BONUS
                            player.health -= damage
                            self.retaliate_attack(enemy, player, dist)
                            print("enemy:", enemy.health)
                            print("player:", player.health)
                            did_attack = True
                            break
                    # Player buildings take damage from enemy attacks
                    if not did_attack:
                        for building in self.buildings:
                            if getattr(building, 'is_constructed', True) and getattr(building, 'hitpoints', 1) > 0:
                                if abs(enemy.x - building.x) + abs(enemy.y - building.y) == 1:
                                    damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/building.defense) * 25 + FLAT_BONUS
                                    building.hitpoints -= enemy.attack
                                    print("enemy:", enemy.health)
                                    print("player:", building.hitpoints)
                                    did_attack = True
                                    break
                    self.enemy_turn_delay = 0  # Pause after attack for clarity/animation
                    self.enemy_turn_index += 1
                    self.enemy_turn_phase = 'move'

        # Checks health of units and removes dead units
        self.unit_health()
        # Checks health of buildings and removes destroyed buildings
        self.building_health()
        # Checks health of enemy units and removes dead units
        self.enemy_unit_health()
        # checks health of enemy buildings and removes destroyed buildings
        self.enemy_building_health()
        
        # Check if the condition to end the game is true
        self.game_over = self.check_game_over()

        # Displays hovered tile and camera scroll
        self.display_hovered_tile()

        # When a player unit is moving
        if self.is_moving:
            self.selected_unit.move_along_path()
            # Stops gathering if the unit moves off the resource tile
            self.gathering_check()
            
            # If the selected unit is not moving, displays a popup menu of its actions
            if not self.selected_unit.path:
                self.is_moving = False
                self.display_unit_actions()

        # Displays the screen
        self.screen.fill((32, 32, 32))

        # 1. Draw the terrain tiles first (Pass 1)
        self.draw_map_with_fog(PLAYABLE_MAP, VISIBILITY_MAP)

        # Only draw reachable tiles if a unit is selected
        if self.selected_unit:
            for tile in (self.reachable_tiles or []):
                self.draw_tile_highlight(tile[0], tile[1], (0, 255, 255, 90))

        # Displays hovered tile
        if self.hovered_tile:
            self.draw_tile_highlight_crimson(*self.hovered_tile)  # crimson outline

        # Combines all objects into a single list and sorts them by their y-coordinate for correct rendering order
        render_queue = []

        for r in self.resources:
            render_queue.append(r)

        # Player buildings and units
        for b in self.buildings:
            render_queue.append(b)
        for u in self.units:
            render_queue.append(u)

        # Enemy Buildings (Only add if tile is '2' which is explored + currently visible)
        for eb in self.e_buildings:
            ex, ey = int(eb.x), int(eb.y)
            if 0 <= ex < len(VISIBILITY_MAP) and 0 <= ey < len(VISIBILITY_MAP[0]):
                if VISIBILITY_MAP[ex][ey] == 2:
                    render_queue.append(eb)

        # Enemy Units (Only add if tile is '2' which is explored + currently visible)
        for eu in self.enemy_units:
            eux, euy = int(eu.x), int(eu.y)
            if 0 <= eux < len(VISIBILITY_MAP) and 0 <= euy < len(VISIBILITY_MAP[0]):
                # Only display if the tile is currently within a player unit's vision range
                if VISIBILITY_MAP[eux][euy] == 2:
                    render_queue.append(eu)

        # Sorting the render queue to ensure correct layering (objects with higher y are drawn on top)
        render_queue.sort(key=lambda obj: (obj.x + obj.y))

        # Drawing objects in order
        for obj in render_queue:
            # Resources
            if isinstance(obj, ResourceSource):
                obj.draw(
                    self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y,
                    BASE_TILE_WIDTH, BASE_TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
                    self.resource_sprites, VISIBILITY_MAP=VISIBILITY_MAP
                )
            
            # Units
            elif hasattr(obj, 'direction'):
                obj.draw(self.screen, self.camera_x, self.camera_y, self.unit_sprites)
            
            # Buildings
            elif hasattr(obj, 'hitpoints'):
                obj.draw(self.screen, self.camera_x, self.camera_y, self.building_sprites)

        # Displays the resource and population bar 
        self.display_resource_bar()

        for res_type in RESOURCE_ICONS.keys():
            self.display_resource_icons(res_type)
        for anim in self.resource_animations.values():
            anim.update()

        self.message_box.draw()
        self.popup_menu.draw(self.screen)
        self.building_menu.draw(self.screen)
        
        # Draw the mini map in the bottom right corner
        self.draw_tactical_map()
        
        pygame.display.flip()