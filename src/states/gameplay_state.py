import pygame
from units.base_units import BaseUnits
from buildings.base_buildings import BaseBuildings
from resources.resource_source import ResourceSource
from message_box import MessageBox
from pop_up_menu import PopupMenu
from path_finding import PathFinding
from target_aquisition import TargetAquisition
from enemy_ai import EnemyAi
from config import *

class GameplayState:
    def __init__(self, screen, game_state_manager):
        self.game_state_manager = game_state_manager
        self.screen = screen
        self.tile_width = BASE_TILE_WIDTH
        self.tile_height = BASE_TILE_HEIGHT
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

        # Terrain sprites
        self.terrain_sprites = {}
        self.terrain_path = TERRAIN_PATH
        self.load_terrain_sprites()

        # Building sprites
        self.building_sprites = {}
        self.building_path = BUILDING_PATH
        self.load_building_sprites()

        # Attack
        self.target_select_mode = False
        self.targetable_enemies = []
        self.selected_target_index = 0

        # Player units initialization
        villager = BaseUnits(5, 5, 5, 50, 25, 1, type="Villager")
        # Player buildings initialization
        town_centre = BaseBuildings(3, 3, 500, 10, type="town_centre")
        town_centre.is_constructed = True
        # Enemy units initialization
        enemy_villager = BaseUnits(7, 7, 5, 50, 25, 1, type="Villager")
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

        self.message_box = MessageBox(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.error_message = True
        self.popup_menu = PopupMenu([], {}, 10, 10)
        self.target_aquisition = TargetAquisition()
        self.enemy_ai = EnemyAi(self.enemy_units)

# === WORLD DISPLAYING ===

    # Removes fog of war around player units and buildings according to their vision range
    def update_VISIBILITY_MAP(self, vision_range):
        for x in range(len(VISIBILITY_MAP)):
            for y in range(len(VISIBILITY_MAP[0])):
                if VISIBILITY_MAP[x][y] == 2:
                    VISIBILITY_MAP[x][y] = 1
        # Iterates over player units and updates unit vision
        for unit in self.units:
            ux, uy = unit.vision_x, unit.vision_y
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx * dx + dy * dy <= vision_range * vision_range:
                        tx = ux + dx
                        ty = uy + dy
                        if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                            VISIBILITY_MAP[tx][ty] = 2
        # Iterates over player buildings and updates unit vision
        for building in self.buildings:
            if building.is_constructed:
                bx, by = int(building.x), int(building.y)
                for dx in range(-vision_range, vision_range + 1):
                    for dy in range(-vision_range, vision_range + 1):
                        if dx * dx + dy * dy <= vision_range * vision_range:
                            tx = bx + dx
                            ty = by + dy
                            if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                                VISIBILITY_MAP[tx][ty] = 2

    # Displays the sprites for the terrain, and magenta for missing sprites
    def draw_map_with_fog(self, map_data, VISIBILITY_MAP, offset_tx=0, offset_ty=0):
        for tx in range(len(map_data)):
            for ty in range(len(map_data[tx])):

                # Skip unseen tiles
                if VISIBILITY_MAP[tx][ty] == 0:
                    continue

                draw_tx = tx + offset_tx
                draw_ty = ty + offset_ty

                screen_x = (
                    (draw_tx - draw_ty) * self.tile_width // 2
                    + (SCREEN_WIDTH // 2)
                    + self.camera_x
                )
                screen_y = (
                    (draw_tx + draw_ty) * self.tile_height // 2
                    + (SCREEN_HEIGHT // 4)
                    + self.camera_y
                )

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
                        (screen_x - self.tile_width // 2, screen_y)
                    )

                else:
                    # If there isnt a sprite, draw a magenta tile
                    pygame.draw.polygon(
                        self.screen,
                        (255, 0, 255),
                        [
                            (screen_x, screen_y),
                            (screen_x + self.tile_width // 2, screen_y + self.tile_height // 2),
                            (screen_x, screen_y + self.tile_height),
                            (screen_x - self.tile_width // 2, screen_y + self.tile_height // 2),
                        ],
                    )

    # Loads the sprites for the world tiles
    def load_terrain_sprites(self):
        for tile_code, filename in TERRAIN_SPRITES.items():
            path = os.path.join(self.terrain_path, filename)
            self.terrain_sprites[tile_code] = pygame.image.load(path).convert_alpha()
    
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

    # 'Cinematic' effect of following enemy units during enemy turn.
    def follow_enemy_camera(self, enemy):
        draw_x = enemy.x + OFFSET_X
        draw_y = enemy.y + OFFSET_Y
        screen_x = (draw_x - draw_y) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
        screen_y = (draw_x + draw_y) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y
        if screen_x < MARGIN:
            self.camera_x += SCROLL_SPEED
        elif screen_x > SCREEN_WIDTH - MARGIN:
            self.camera_x -= SCROLL_SPEED
        if screen_y < MARGIN:
            self.camera_y += SCROLL_SPEED
        elif screen_y > SCREEN_HEIGHT - MARGIN:
            self.camera_y -= SCROLL_SPEED

    def display_hovered_tile(self):
        # The hovered tile is selected
        self.hovered_tile = self.selected_tile

        # Convert hovered tile to screen coordinates
        draw_x = self.hovered_tile[0] + OFFSET_X
        draw_y = self.hovered_tile[1] + OFFSET_Y

        screen_x = (draw_x - draw_y) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
        screen_y = (draw_x + draw_y) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y

        # Camera follow
        if screen_x < MARGIN:
            self.camera_x += SCROLL_SPEED
        elif screen_x > SCREEN_WIDTH - MARGIN:
            self.camera_x -= SCROLL_SPEED

        if screen_y < MARGIN:
            self.camera_y += SCROLL_SPEED
        elif screen_y > SCREEN_HEIGHT - MARGIN:
            self.camera_y -= SCROLL_SPEED

# === MAP DISPLAYING ===

    # Displays the map when opened.
    def draw_tactical_map(self):
        self.screen.fill((32, 32, 32))
        tile_size = 25
        half_width = tile_size // 2
        half_height = tile_size // 4
        map_width_px = (PLAYABLE_WIDTH + PLAYABLE_HEIGHT) * half_width
        map_height_px = (PLAYABLE_WIDTH + PLAYABLE_HEIGHT) * half_height // 2
        offset_draw_x = (SCREEN_WIDTH - map_width_px) // 2
        offset_draw_y = (SCREEN_HEIGHT - map_height_px) // 2 - SCREEN_HEIGHT // 2

        # Draw only visible tiles
        for x in range(PLAYABLE_WIDTH):
            for y in range(PLAYABLE_HEIGHT):
                vis = VISIBILITY_MAP[x][y]
                if vis == 0:
                    continue  # Skip tiles not visible
                tile = PLAYABLE_MAP[x][y]
                color = TILE_DRAW_COLORS.get(tile, (255, 0, 255))
                draw_x = (x - y) * half_width + offset_draw_x + map_width_px // 2
                draw_y = (x + y) * half_height + offset_draw_y + map_height_px // 2
                pygame.draw.polygon(self.screen, color, [
                    (draw_x, draw_y),
                    (draw_x + half_width, draw_y + half_height),
                    (draw_x, draw_y + 2 * half_height),
                    (draw_x - half_width, draw_y + half_height)
                ])

        # Only draw player units/buildings/resources if on visible tiles
        for unit in self.units:
            ux, uy = int(unit.x), int(unit.y)
            if 0 <= ux < PLAYABLE_WIDTH and 0 <= uy < PLAYABLE_HEIGHT and VISIBILITY_MAP[ux][uy] != 0:
                self.draw_unit(ux, uy, half_width, half_height, offset_draw_x, offset_draw_y)
        for building in self.buildings:
            bx, by = int(building.x), int(building.y)
            if 0 <= bx < PLAYABLE_WIDTH and 0 <= by < PLAYABLE_HEIGHT and VISIBILITY_MAP[bx][by] != 0:
                self.draw_building(bx, by, half_width, half_height, offset_draw_x, offset_draw_y)
        for res in self.resources:
            rx, ry = int(res.x), int(res.y)
            if 0 <= rx < PLAYABLE_WIDTH and 0 <= ry < PLAYABLE_HEIGHT and VISIBILITY_MAP[rx][ry] != 0:
                self.draw_resource(rx, ry, half_width, half_height, offset_draw_x, offset_draw_y)
        
        # Draw camera view (isometric polygon)
        corners = [
            (0, 0), (SCREEN_WIDTH, 0), (SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)
        ]
        iso_points = []
        for sx, sy in corners:
            world_x = (sx - SCREEN_WIDTH // 2) - self.camera_x
            world_y = (sy - SCREEN_HEIGHT // 4) - self.camera_y
            tile_y = ((2 * world_y - world_x) // self.tile_height) // 2
            tile_x = ((2 * world_y + world_x) // self.tile_height) // 2
            draw_x = (tile_x - tile_y) * half_width + offset_draw_x + map_width_px // 2
            draw_y = (tile_x + tile_y) * half_height + offset_draw_y + map_height_px // 2
            iso_points.append((draw_x, draw_y))
        pygame.draw.polygon(self.screen, (255, 255, 0), iso_points, 2)
        pygame.display.flip()

    # Displays units on the map
    def draw_unit(self, x, y, half_width, half_height, offset_draw_x, offset_draw_y):
        draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
        draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2
        triangle_points = [
            (draw_x, draw_y - half_height),
            (draw_x - half_width, draw_y + half_height),
            (draw_x + half_width, draw_y + half_height),
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), triangle_points)

    # Displays buildings on the map
    def draw_building(self, x, y, half_width, half_height, offset_draw_x, offset_draw_y):
        draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
        draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2
        size = half_width // 2
        pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))

    # Displays resources on the map
    def draw_resource(self, x, y, half_width, half_height, offset_draw_x, offset_draw_y):
        # Only draw resources if tile is visible
        if 0 <= x < PLAYABLE_WIDTH and 0 <= y < PLAYABLE_HEIGHT and VISIBILITY_MAP[x][y] == 2:
            draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
            draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2
            radius = half_width // 2
            pygame.draw.circle(self.screen, (255, 255, 255), (draw_x, draw_y), radius)

    # Displays highlighted reachable tiles
    def draw_tile_highlight(self, tx, ty, color, alpha=128):
        draw_tx = tx + OFFSET_X
        draw_ty = ty + OFFSET_Y
        screen_x = (draw_tx - draw_ty) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
        screen_y = (draw_tx + draw_ty) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y
        overlay = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
        pygame.draw.polygon(overlay, color, [
            (self.tile_width // 2, 0),
            (self.tile_width, self.tile_height // 2),
            (self.tile_width // 2, self.tile_height),
            (0, self.tile_height // 2)
        ])
        self.screen.blit(overlay, (screen_x - self.tile_width // 2, screen_y))

    # Displays the red hovered tile
    def draw_tile_highlight_crimson(self, tx, ty, color=(220, 20, 60)):
        draw_tx = tx + OFFSET_X
        draw_ty = ty + OFFSET_Y
        screen_x = (draw_tx - draw_ty) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
        screen_y = (draw_tx + draw_ty) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y

        # Define the diamond shape points
        points = [
            (screen_x, screen_y),  # top
            (screen_x + self.tile_width // 2, screen_y + self.tile_height // 2),  # right
            (screen_x, screen_y + self.tile_height),  # bottom
            (screen_x - self.tile_width // 2, screen_y + self.tile_height // 2),  # left
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

        # If the unit is a villager, allow building if tile is empty
        if self.selected_unit.type == "Villager":
            if not self.is_tile_occupied(*self.hovered_tile):
                options.insert(1, "Build")
                actions["Build"] = self.build_action

        # If the villager is on a resource tile, allow gathering
        landed_tile = (int(self.selected_unit.x), int(self.selected_unit.y))
        if self.selected_unit.type == "Villager":
            for res in self.resources:
                if (res.x, res.y) == landed_tile:
                    options.insert(2, "Gather")
                    actions["Gather"] = lambda u=self.selected_unit, r=res: self.gather_action(u, r)
                    break

        # Ranged attack logic
        if self.selected_unit.attack_range > 1:
            if self.target_aquisition.any_ranged_enemy_in_range(
                self.selected_tile,
                self.selected_unit.attack_range,
                self.enemy_units
            ):
                options.insert(0, "Attack")
                actions["Attack"] = lambda: self.attack_action(self.selected_unit)

        # Melee attack logic
        else:
            if self.target_aquisition.is_enemy_adjacent(self.selected_tile, self.enemy_units):
                options.insert(0, "Attack")
                actions["Attack"] = lambda: self.attack_action(self.selected_unit)

        self.popup_menu.open(options, actions)
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )

    # Moves a unit and increases the action count by 1, deselects the unit, then closes the popup menu
    def move_action(self):
        self.reachable_tiles = set()
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit:
            selected_unit.rest()
            selected_unit.selected = False
        # Updates vision position
        selected_unit.vision_x = int(selected_unit.x)
        selected_unit.vision_y = int(selected_unit.y)

        self.selected_unit_id = None
        self.popup_menu.close()

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
        self.popup_menu.open(["Town Centre", "Mill", "Cancel"], {
            "Town Centre": lambda: self.building_construction("town_centre"),
            "Mill": lambda: self.building_construction("mill"),
            "Cancel": self.cancel_action
        })
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )
    
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
            new_building_id = max([b.id for b in self.buildings], default=0) + 1
            new_building = BaseBuildings(self.selected_tile[0], self.selected_tile[1], b_attr[4], b_attr[5])
            new_building.id = new_building_id
            new_building.type = building_name
            new_building.building_queued()
            new_building.is_constructed = False
            self.buildings.append(new_building)
            self.popup_menu.close()
            if selected_unit:
                selected_unit.rest()
                self.construction[selected_unit] = new_building
                selected_unit.selected = False
            # Updates vision position
            selected_unit.vision_x = int(selected_unit.x)
            selected_unit.vision_y = int(selected_unit.y)
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
        self.popup_menu.back()
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )

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
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )

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
            self.popup_menu.set_position(
                (SCREEN_WIDTH - self.popup_menu.width) // 2,
                (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
            )

    # Displays a popup menu of the trainable units at the selected building, and spawns the unit
    def unit_selection(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        spawn_x, spawn_y = selected_building.x, selected_building.y
        building_name = selected_building.type
        # Finds the building's attribute list consisting of type, cost, and trainable units
        if building_name in BUILDINGS:
            b_attr = BUILDINGS[building_name]
        else:
            b_attr = RESOURCE_BUILDINGS[building_name]
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
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )

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

    # Research in buildings. Needs fixing
    def research_action(self):
        self.message_box.open("Researching upgrades")
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        if selected_building:
            selected_building.selected = False
        self.selected_building_id = None
        self.popup_menu.close()
    
# === RESOURCE GATHERING ===

    # Processes player's resource gathering at the end of enemy turn
    def process_automatic_gathering(self):
        # Iterates over all units and checks if they are gathering. 
        for unit in self.units:
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
                        self.food_amount += amount_gathered
                    elif res.resource_type == "wood":
                        self.wood_amount += amount_gathered
                    elif res.resource_type == "gold":
                        self.gold_amount += amount_gathered
                    if res.amount <= 0:
                        self.resources.remove(res)
                        self.message_box.open(f"{res.resource_type} has been depleted.")
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

        self.popup_menu.open(["End Day", "Cancel"],
                            {
                                "End Day": self.end_day,
                                "Cancel": self.popup_menu.close
                            }
        )

        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
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

        self.message_box.close()

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

# === GAME LOOP ===

    def run(self):
        # global actions, callbacks
        if not self.game_over:
            # Events during the player's turn
            if self.player_turn:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        return

                    # popup menu handling
                    if self.popup_menu.is_open:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_w:
                                self.popup_menu.move_selection(-1)
                            elif event.key == pygame.K_s:
                                self.popup_menu.move_selection(1)
                            elif event.key == pygame.K_LSHIFT:
                                self.popup_menu.select()
                        continue  # While popup is open, IGNORE ALL OTHER CONTROLS

                    # Target selection
                    if self.target_select_mode:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_TAB and self.targetable_enemies:
                                self.cycle_target()
                            elif event.key == pygame.K_LSHIFT:
                                self.open_attack_confirm_menu()
                            return

                    # Normal gameplay input (when not in popup, message, or target select mode) 
                    if event.type == pygame.KEYDOWN:

                        # Deselect units or buildings
                        if event.key == pygame.K_ESCAPE:
                            self.deselect()
                            self.message_box.close()

                        # Get the state of all keys
                        keys = pygame.key.get_pressed()

                        # Check each key (this will run every frame the key is held)
                        if keys[pygame.K_w] and self.selected_tile[1] > 0:
                            self.selected_tile = (self.selected_tile[0], self.selected_tile[1] - 1)
                        if keys[pygame.K_s] and self.selected_tile[1] < PLAYABLE_HEIGHT - 1:
                            self.selected_tile = (self.selected_tile[0], self.selected_tile[1] + 1)
                        if keys[pygame.K_a] and self.selected_tile[0] > 0:
                            self.selected_tile = (self.selected_tile[0] - 1, self.selected_tile[1])
                        if keys[pygame.K_d] and self.selected_tile[0] < PLAYABLE_WIDTH - 1:
                            self.selected_tile = (self.selected_tile[0] + 1, self.selected_tile[1])

                        # Cycles through available units
                        if event.key == pygame.K_TAB:
                            self.cycle_player_units()

                        # Opens the map
                        if event.key == pygame.K_m:
                            if not self.is_moving:
                                self.tactical_map_mode = not self.tactical_map_mode

                        # Selection/Deselection and movement with shift key
                        if event.key == pygame.K_LSHIFT:
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

        # Displays the map if it is opened
        if self.tactical_map_mode:
            self.draw_tactical_map()
            self.clock.tick(30)
            return

        # Updates the unit visibility
        self.update_VISIBILITY_MAP(vision_range=3)

        # Displays the screen
        self.screen.fill((32, 32, 32))

        # Implements the fog of war
        self.draw_map_with_fog(
            PLAYABLE_MAP,
            VISIBILITY_MAP,
            OFFSET_X,
            OFFSET_Y
        )

        # Only draw reachable tiles if a unit is selected
        if self.selected_unit:
            for tile in (self.reachable_tiles or []):
                self.draw_tile_highlight(tile[0], tile[1], (0, 255, 255, 90))

        # Displays hovered tile
        if self.hovered_tile:
            self.draw_tile_highlight_crimson(*self.hovered_tile)  # crimson outline

        # Draws resources
        for resource in self.resources:
            resource.draw(
                self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y,
                self.tile_width, self.tile_height, SCREEN_WIDTH, SCREEN_HEIGHT,
                self.resources, VISIBILITY_MAP=VISIBILITY_MAP
            )
        # Draws player and enemy buildings
        for building in self.buildings:
            building.draw(
                self.screen,
                OFFSET_X,
                OFFSET_Y,
                self.camera_x,
                self.camera_y,
                self.tile_width,
                self.tile_height,
                self.building_sprites
            )

        for eb in self.e_buildings:
            ex, ey = int(eb.x), int(eb.y)
            if (
                0 <= ex < len(VISIBILITY_MAP)
                and 0 <= ey < len(VISIBILITY_MAP[0])
                and VISIBILITY_MAP[ex][ey] == 2
            ):
                eb.draw(
                self.screen,
                OFFSET_X,
                OFFSET_Y,
                self.camera_x,
                self.camera_y,
                self.tile_width,
                self.tile_height,
                self.building_sprites
            )
        # Draws player and enemy units
        for enemy in self.enemy_units:
            ex, ey = int(enemy.x), int(enemy.y)
            if (
                0 <= ex < len(VISIBILITY_MAP)
                and 0 <= ey < len(VISIBILITY_MAP[0])
                and VISIBILITY_MAP[ex][ey] == 2
            ):
                enemy.draw(self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y, self.tile_width, self.tile_height)
        for unit in self.units:
            unit.draw(self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y, self.tile_width, self.tile_height)

        # Displays the resource and population bar 
        bar_height = 25
        bar_color = (20, 20, 20)
        text_color = (255, 255, 255)
        font = pygame.font.SysFont(None, 24)

        # Fill top bar background
        pygame.draw.rect(self.screen, bar_color, (0, 0, SCREEN_WIDTH, bar_height))

        # Population
        self.population = len(self.units)
        max_pop = 0  # Reset before accumulation
        for building in self.buildings:
            if building.is_constructed:
                max_pop += building.population_limit

        # Resource display
        resource_text = (
            f"| Food: {self.food_amount} "
            f"| Wood: {self.wood_amount} "
            f"| Gold: {self.gold_amount} "
            f"| Pop: {self.population} / {max_pop} |"
        )
        text_surface = font.render(resource_text, True, text_color)

        # Calculate the x-coordinate to center the text horizontally
        text_width = text_surface.get_width()
        center_x = (SCREEN_WIDTH - text_width) // 2

        # Calculate the y-coordinate to center the text vertically
        center_y = (bar_height - text_surface.get_height()) // 2

        # Draw the text centered in the display bar
        self.screen.blit(text_surface, (center_x, center_y))

        self.popup_menu.draw(self.screen)
        self.message_box.draw()