import pygame
from renderer import Renderer
from turn_manager import TurnManager
from fade_manager import FadeManager
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
    def __init__(self, screen, game_state_manager, asset_manager, player_faction=None, enemy_faction=None, player_color=None, enemy_color=None):
        # Store the game state manager for transitioning between different game states (e.g., menu, gameplay, game over)
        self.game_state_manager = game_state_manager
        # Store the asset manager for loading and accessing game assets like sprites and icons
        self.assets = asset_manager

        self.screen = screen
        w, h = screen.get_size()
        # Initialize the clock for controlling the frame rate
        self.clock = pygame.time.Clock()
        # Initialize the renderer, which handles drawing the game world, units, buildings, and UI elements on the screen
        self.renderer = Renderer(self.screen, self.assets)
        # Initialize the turn manager, which processes end of day events.
        self.turn_manager = TurnManager()
        # Initial position of the selected tile
        self.selected_tile = (4, 4)
        self.hovered_tile = self.selected_tile
        self.path = []
        # is_moving indicates whether a unit is currently moving along a path
        self.is_moving = False
        # last_key_pressed is used to track the last key pressed for input handling
        self.last_key_pressed = None
        # reachable_tiles is a set of tiles that the selected unit can move to
        self.reachable_tiles = set()
        # Player and enemy resources
        self.food_amount = 500
        self.wood_amount = 500
        self.gold_amount = 500
        self.enemy_food = 500
        self.enemy_wood = 500
        self.enemy_gold = 500
        # Day counter
        self.day = 0
        # Selected entities and their IDs for tracking which unit or building is currently selected
        self.selected_unit = None
        self.selected_building = None
        self.selected_unit_id = None
        self.selected_building_id = None
        # running indicates whether the game loop is active
        self.running = True
        # camera_x and camera_y are used to control the camera's position in the game world
        self.camera_x = 0
        self.camera_y = 0
        # Free camera mode allows the player to move the camera independently of the selected tile
        self.free_cam_active = False
        self.camera_return = False
        # camera_target_x and camera_target_y are used for smooth camera transitions
        self.camera_target_x = 0
        self.camera_target_y = 0
        # tile_move_delay is used to control the delay between tile movements for smoother animations
        self.tile_move_delay = 5
        # Player and enemy factions
        self.player_faction = player_faction
        self.enemy_faction = enemy_faction
        # Fade day
        self.fade_manager = FadeManager()
        self.day_processed_mid_fade = False
        # Minimap dimensions and positioning
        self.minimap_size = int(h * 0.42)
        self.radius = self.minimap_size // 2
        self.smaller_radius = int(self.radius * 0.85)
        self.mini_map_scale = int(self.radius // (PLAYABLE_WIDTH // 2 + 1) * 0.40)
        self.mini_map_center_x = w - self.radius - 20
        self.mini_map_center_y = h - self.radius - 20
        # Researched techs and their multipliers for both player and enemy
        self.researched_techs = set()
        self.tech_multipliers = {
            "unit_vision": 0,
            "unit_movement": 0,
            "building_vision": 0,
            "gather_rate_food": 1.0,
            "gather_rate_wood": 1.0,
            "gather_rate_gold": 1.0
        }
        self.enemy_tech_multipliers = {
            "unit_vision": 0,
            "unit_movement": 0,
            "building_vision": 0,
            "gather_rate_food": 1.0,
            "gather_rate_wood": 1.0,
            "gather_rate_gold": 1.0
        }
        # Techs that are currently being researched by the player and enemy
        self.pending_techs = []
        self.enemy_researched_techs = set()
        self.enemy_pending_techs =[]
        # Target selection mode for combat or abilities, entered when True
        self.target_select_mode = False
        self.targetable_enemies = []
        self.selected_target_index = 0
        # Player and enemy town centers, initialized with their positions, health, and population limits
        town_centre = BaseBuildings(3, 3, 500, 10, type="town_centre")
        town_centre.is_constructed = True
        e_town_centre = BaseBuildings(6, 10, 500, 10, type="town_centre")
        e_town_centre.is_constructed = True
        # Initialize player and enemy units, buildings, resources, and construction queues
        self.units = []
        self.buildings = [town_centre]
        self.resources = resources
        self.construction = {}
        self.enemy_units = []
        self.e_buildings = [e_town_centre]
        # Population tracking for both player and enemy, as well as the maximum population allowed by buildings
        self.population = len(self.units)
        self.e_population = len(self.enemy_units)
        self.enemy_max_population = 0
        for building in self.buildings:
            self.enemy_max_population += building.population_limit
        self.allow_villager_training = True
        # Turn control
        self.player_turn = True
        self.enemy_moving = False
        self.enemy_paths_planned = False
        self.enemy_turn_index = 0      
        self.enemy_turn_phase = 'move' 
        self.enemy_turn_delay = 0      
        # Player and enemy ages, initialized to "Dark Age"
        self.player_age = "Dark Age"
        self.enemy_age = "Dark Age"
        # Game over flag to indicate if the game has ended when True
        self.game_over = False
        # Update the visibility map based on the initial positions of units and buildings (Fog of War)
        self.update_VISIBILITY_MAP()
        # Initialize the message box and popup menus for in-game notifications and interactions
        self.message_box = MessageBox(
            self.screen, 
            SCREEN_WIDTH, 
            SCREEN_HEIGHT, 
            self.assets.ui_elements["message_box"]
        )
        self.error_message = True
        self.popup_menu = PopupMenu(
            [], {}, 0, 0, self.assets.ui_elements, self.message_box, 
            sprite_key="popup_menu", side="left"
        )
        self.building_menu = PopupMenu(
            [], {}, 0, 0, self.assets.ui_elements, self.message_box, 
            sprite_key="building_menu", side="right"
        )
        # Initialize pathfinding and target acquisition systems for unit movement and combat
        self.target_aquisition = TargetAquisition()
        
# === INITIALIZATION ===

    # This method is called when entering the gameplay state. It initializes the player and enemy factions, colors, and sets up
    # the game environment.
    def enter(self, **kwargs):
        # Determine the player and enemy factions based on the provided keyword arguments or default values. If no faction is 
        # specified, it defaults to "seljuks" for the player and "byzantines" for the enemy.
        p_faction = kwargs.get("player_faction") or getattr(self, "player_faction", "seljuks") or "seljuks"
        e_faction = kwargs.get("enemy_faction") or getattr(self, "enemy_faction", "byzantines") or "byzantines"
        
        # Determine the player and enemy colors based on the provided keyword arguments or default values. If no color is specified,
        # it defaults to "blue" for the player and "red" for the enemy.
        p_color = kwargs.get("player_color") or getattr(self, "player_color", "blue") or "blue"
        e_color = kwargs.get("enemy_color") or getattr(self, "enemy_color", "red") or "red"

        self.player_faction = p_faction
        self.enemy_faction = e_faction
        self.player_color = p_color
        self.enemy_color = e_color

        print(f"[LIFE-CYCLE] Gameplay State Active | Player: {self.player_faction} ({self.player_color}) vs Enemy: {self.enemy_faction} ({self.enemy_color})")

        # Reset game state variables to their initial values when entering the gameplay state. This includes closing any open menus,
        # clearing unit and enemy lists, and resetting movement and pathfinding states.
        self.popup_menu.close()
        self.popup_menu.is_open = False
        self.building_menu.close()
        self.building_menu.is_open = False

        self.units = []
        self.enemy_units = []
        self.path = []
        self.is_moving = False

        # Set up the player and enemy factions by calling their respective setup methods. These methods initialize the starting 
        # units and buildings
        self.player_setup(self.player_faction)
        self.enemy_setup(self.enemy_faction)

        # Update the visibility map to reflect the initial positions of units and buildings, ensuring that the fog of war is 
        # correctly applied
        self.update_VISIBILITY_MAP()

    # Sets up the player's starting hero unit based on the selected faction. It retrieves the hero's stats from the UNITS database    
    def player_setup(self, faction):
        # Safety. Could remove in the future.
        if not faction:
            print("[ERROR] No faction string provided to player_setup!")
            return

        # Retrieve the faction data from the FACTIONS database using the provided faction string. If the faction is not found, an error
        # message is printed, and the method returns early.
        faction_key = faction.lower().strip()
        faction_data = FACTIONS.get(faction_key)

        if faction_data is None:
            print(f"[ERROR] Faction '{faction_key}' not found in FACTIONS config database! Available keys: {list(FACTIONS.keys())}")
            return

        # Retrieve the hero's key from the faction data, which is used to look up the hero's stats in the UNITS database. 
        # If the hero's stats are not found, an error message is printed, and the method returns early.
        hero_key = faction_data.get("hero_key") or faction_data.get("hero")
        hero_stats = UNITS.get(hero_key)

        if not hero_stats:
            print(f"[ERROR] Hero stats key '{hero_key}' not found in UNITS database!")
            return

        start_x, start_y = 3, 3
        print(f"[INIT] Spawning Player Hero: {hero_stats[0]} at ({start_x}, {start_y})")

        # Create the player's hero unit using the retrieved stats and starting position. The hero is added to the player's units list.
        player_hero = BaseUnits(start_x, start_y, hero_stats[5], hero_stats[6], hero_stats[7], hero_stats[8], type=hero_key)
        self.units.append(player_hero)

    # Sets up the enemy's starting hero unit based on the selected faction. It retrieves the hero's stats from the UNITS database
    # and positions the enemy hero at a distinct starting tile. The enemy hero is added to the enemy_units list.
    def enemy_setup(self, faction):
        if not faction:
            print("[ERROR] No faction string provided to enemy_setup!")
            return

        faction_key = faction.lower().strip()
        faction_data = FACTIONS.get(faction_key)

        if faction_data is None:
            print(f"[ERROR] Faction '{faction_key}' not found in FACTIONS database!")
            return

        hero_key = faction_data.get("hero_key") or faction_data.get("hero")
        hero_stats = UNITS.get(hero_key)

        if not hero_stats:
            print(f"[ERROR] Hero stats key '{hero_key}' not found in UNITS database!")
            return

        # Position opponent hero at distinct starting tile coordinates
        start_x, start_y = 6, 10
        print(f"[INIT] Spawning Enemy Hero: {hero_stats[0]} at ({start_x}, {start_y})")

        enemy_hero = BaseUnits(start_x, start_y, hero_stats[5], hero_stats[6], hero_stats[7], hero_stats[8], type=hero_key)
        
        self.enemy_units.append(enemy_hero)  # Append to enemy collection instead of self.units

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

    # Applies a circular vision effect on the VISIBILITY_MAP centered at (cx, cy) with the specified radius. 
    # Tiles within the circle are marked as visible (2).
    def apply_vision_circle(self, cx, cy, radius):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    tx, ty = cx + dx, cy + dy
                    if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                        VISIBILITY_MAP[tx][ty] = 2

    # Camera follows hovered tile
    def display_hovered_tile(self):
        # The hovered tile is selected
        self.hovered_tile = self.selected_tile

        # Convert hovered tile to screen coordinates
        draw_x, draw_y = self.renderer.draw_coords(self.hovered_tile[0], self.hovered_tile[1])
        screen_x, screen_y = self.renderer.screen_coords(draw_x, draw_y, self.camera_x, self.camera_y)

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

    # 'Cinematic' effect of following enemy units during enemy turn.
    def follow_enemy_camera(self, enemy):
        draw_x, draw_y = self.renderer.draw_coords(enemy.x, enemy.y)
        screen_x, screen_y = self.renderer.screen_coords(draw_x, draw_y, self.camera_x, self.camera_y)

        if screen_x < MARGIN:
            self.camera_x += SCROLL_SPEED
        elif screen_x > SCREEN_WIDTH - MARGIN:
            self.camera_x -= SCROLL_SPEED
        if screen_y < MARGIN:
            self.camera_y += SCROLL_SPEED
        elif screen_y > SCREEN_HEIGHT - MARGIN:
            self.camera_y -= SCROLL_SPEED

    # Centers the camera back onto the selected_tile.
    def camera_lerp(self):
        # Calculate the destination coordinates
        draw_x, draw_y = self.draw_coords(self.selected_tile[0], self.selected_tile[1])
        world_x, world_y = self.screen_coords(draw_x, draw_y)
        
        target_x = (SCREEN_WIDTH // 2) - world_x
        target_y = (SCREEN_HEIGHT // 2) - world_y

        # Lerp towards destination
        lerp_speed = 0.1 
        self.camera_x += (target_x - self.camera_x) * lerp_speed
        self.camera_y += (target_y - self.camera_y) * lerp_speed

        # Check if we are close enough to stop
        if abs(self.camera_x - target_x) < 1 and abs(self.camera_y - target_y) < 1:
            self.camera_x = target_x
            self.camera_y = target_y
            self.camera_return = False

    # Removes a resource from the map when the tile is built on
    def cover_resources(self, x, y):
        for resource in self.resources:
            if resource.x == x and resource.y == y:
                self.resources.remove(resource)

    def update_fade_screen(self):
        # Update the fade manager each frame and catch any peak-black event
        fade_event = self.fade_manager.update()

        # Fire data alteration calculations exactly once when the screen is fully dark
        if fade_event == "PEAK_BLACK":
            if not self.day_processed_mid_fade:
                self.turn_manager.process_day_transition(self)
                self.day_processed_mid_fade = True

        # Reset the mid-fade flag once the fade-in finishes completely
        if not self.fade_manager.is_fading:
            self.day_processed_mid_fade = False
                
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
        if self.selected_unit.type == "villager":
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

        self.building_menu.sprites["building_icons"] = icon_mapping
        
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
        if building.building_tired():
            return

        building.selected = True
        
        options = ["Research", "Cancel"]
        actions = {
            "Research": self.research_action,
            "Cancel": self.deselect
        }

        # Add Train if it's a production building
        if building.type in BUILDINGS:
            options.insert(0, "Train")
            actions["Train"] = self.unit_selection

        # Specific Town Centre Logic
        if building.type == "town_centre":
            options.insert(2, "Age Up")
            actions["Age Up"] = lambda: self.attempt_age_up('player')

        self.popup_menu.open(options, actions)

    # Displays a popup menu of the trainable units at the selected building, and spawns the unit
    def unit_selection(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        spawn_x, spawn_y = selected_building.x, selected_building.y
        building_name = selected_building.type
        
        # Finds the building's attribute list consisting of type, cost, and trainable units
        if building_name in BUILDINGS:
            b_attr = BUILDINGS[building_name]
            trainable_units = b_attr[6]
        else:
            # Handle resource buildings if they have units, or default to empty list
            b_attr = RESOURCE_BUILDINGS.get(building_name, [None]*10)
            trainable_units = b_attr[6] if b_attr[6] is not None else []

        affordable_unit_keys = []
        options = []
        
        for unit_name in trainable_units:
            # Normalize to lowercase for dictionary lookup
            u_key = unit_name.lower()
            if u_key in UNITS:
                u_attr = UNITS[u_key]
                food, wood, gold = u_attr[1], u_attr[2], u_attr[3]
                
                # Check affordability
                if (self.food_amount >= food and
                    self.wood_amount >= wood and
                    self.gold_amount >= gold):
                    
                    # Store technical key and display name
                    affordable_unit_keys.append(u_key)
                    options.append(u_attr[0]) # The friendly name (e.g., "Villager")

        # Map display names to actions
        actions = {}
        for i in range(len(affordable_unit_keys)):
            u_key = affordable_unit_keys[i]
            display_name = options[i]
            # When clicked, trigger train_action with the correct technical key
            actions[display_name] = (lambda k=u_key: self.train_action(k, spawn_x, spawn_y))

        # Add Cancel option
        options.append("Cancel")
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
        self.selected_building_id = None
        self.popup_menu.close()
        self.message_box.close()

    # Handles the transition to the next age for both the player or enemy
    def attempt_age_up(self, side):
        
        # Determine current state based on side
        if side == 'player':
            self.popup_menu.close()
            current_age = self.player_age
            food = self.food_amount
            wood = self.wood_amount
            gold = self.gold_amount
            tech_count = len(self.researched_techs)
        else:
            current_age = self.enemy_age
            food = self.enemy_food
            wood = self.enemy_wood
            gold = self.enemy_gold
            tech_count = len(self.enemy_researched_techs)

        # Get requirements for the CURRENT age to move to the NEXT
        age_data = AGES.get(current_age)
        if not age_data or "next_age" not in age_data:
            return "Max Age Reached"

        req_food = age_data["food"]
        req_wood = age_data["wood"]
        req_gold = age_data["gold"]
        req_techs = age_data["req_techs"]

        # Check Requirements
        if tech_count < req_techs:
            if side == 'player':
                self.message_box.open(f"Requires {req_techs} technologies to be researched!", True)
                if self.selected_building:
                    self.selected_building.selected = False
            return False

        if food >= req_food and wood >= req_wood and gold >= req_gold:
            # Success: Deduct Resources
            if side == 'player':
                self.food_amount -= req_food
                self.wood_amount -= req_wood
                self.gold_amount -= req_gold
                self.player_age = age_data["next_age"]
            else:
                self.enemy_food -= req_food
                self.enemy_wood -= req_wood
                self.enemy_gold -= req_gold
                self.enemy_age = age_data["next_age"]

            # Handle Town Centre "Tiring" (Marking all TCs as acted)
            relevant_buildings = self.buildings if side == 'player' else self.e_buildings
            for b in relevant_buildings:
                if "town" in b.type.lower():
                    b.rest() # Assuming rest() sets action_count to 0
            
            print(f"{side.capitalize()} advanced to {age_data['next_age']}!")
            if self.selected_building:
                self.selected_building.selected = False
            return True
        else:
            # Failure: Resource Message
            if side == 'player':
                self.message_box.open("Insufficient funds to Age Up!", True)
                if self.selected_building:
                    self.selected_building.selected = False
            return False

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
        elif self.player_age == "Fuedal Age":
            self.game_state_manager.set_state("game over")
            return
        elif self.enemy_age == "Fuedal Age":
            self.game_state_manager.set_state("game over")
            return
        # Game continues running
        else:
            return False
        
# === EVENT HANDLING ===

    # Handles all input from keys.
    def handle_input(self, events):
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
                self.handle_input(events)
                self.update_fade_screen()
            # Enemy turn
            else: 
                self.turn_manager.update_enemy_turn(self)
        
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

        # Draws the game world, including terrain, units, buildings, and UI elements
        self.renderer.draw_game_world(self, VISIBILITY_MAP)