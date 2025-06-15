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

# implement enemy ai for gathering resources, training units.

class GameplayState:
    def __init__(self, screen):
        self.screen = screen
        self.zoom_level = 1
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
        self.enemy_food = 0
        self.enemy_wood = 0
        self.enemy_gold = 0
        self.selected_unit = None
        self.selected_building = None
        self.selected_unit_id = None
        self.selected_building_id = None
        self.running = True
        self.tactical_map_queued = False
        self.last_tactical_key = None
        self.camera_x = 0
        self.camera_y = 0

        # Attack
        self.target_select_mode = False
        self.targetable_enemies = []
        self.selected_target_index = 0

        # Player units initialization
        villager = BaseUnits(5, 5, 5, 50, 25, 1, type="villager")
        archer = BaseUnits(6, 6, 7, 150, 100, 3, type="archer")
        # Player buildings initialization
        town_centre = BaseBuildings(3, 3, 500, 10, type="town_centre")
        town_centre.is_constructed = True
        # Resource initialization
        resource = [
            ResourceSource(1, 3, "food", 500),
            ResourceSource(3, 1, "gold", 2000),
            ResourceSource(5, 3, "wood", 400)
        ]
        # Enemy units initialization
        enemy_villager = BaseUnits(1, 1, 5, 50, 25, 1, type="villager")
        spearmen = BaseUnits(7, 7, 7, 100, 100, 1, type="spearmen")
        spearmen2 = BaseUnits(7, 5, 7, 100, 100, 1, type="spearmen")
        # Enemy buildings initialization
        e_town_centre = BaseBuildings(16, 16, 500, 10, type="town_centre")
        e_town_centre.is_constructed = True

        # Player unit and building lists
        self.units = [villager, archer]
        self.buildings = [town_centre]
        self.resources = resource
        # Enemy unit and building lists
        self.enemy_units = [spearmen, spearmen2, enemy_villager]
        self.e_buildings = [e_town_centre]
        self.population = len(self.units)
        self.player_turn = True
        self.enemy_moving = False
        self.enemy_paths_planned = False
        self.enemy_turn_index = 0      # index of the current enemy being processed
        self.enemy_turn_phase = 'move' # 'move', 'attack', or 'done'
        self.enemy_turn_delay = 0      # delay timer for animation

        self.game_over = False

        self.message_box = MessageBox(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.popup_menu = PopupMenu([], {}, 10, 10)
        self.target_aquisition = TargetAquisition()
        self.enemy_ai = EnemyAi(self.enemy_units)

    # === Drawing methods ===

    def draw_tactical_map(self):
        self.screen.fill((32, 32, 32))
        tile_size = 15
        half_width = tile_size // 2
        half_height = tile_size // 4
        # Calculate center offset for tactical map centering
        map_width_px = (PLAYABLE_WIDTH + PLAYABLE_HEIGHT) * half_width
        map_height_px = (PLAYABLE_WIDTH + PLAYABLE_HEIGHT) * half_height // 2
        offset_draw_x = (SCREEN_WIDTH - map_width_px) // 2
        offset_draw_y = (SCREEN_HEIGHT - map_height_px) // 2 - SCREEN_HEIGHT // 2
        # Draw the tactical map tiles (hexagonal or diamond grid)
        for x in range(PLAYABLE_WIDTH):
            for y in range(PLAYABLE_HEIGHT):
                vis = VISIBILITY_MAP[x][y]
                tile = PLAYABLE_MAP[x][y]
                if vis == 0:
                    color = (0, 0, 0)
                else:
                    color = (34, 177, 76) if tile == "G" else (127, 127, 127) if tile == "S" else (0, 162, 232)
                draw_x = (x - y) * half_width + offset_draw_x + map_width_px // 2
                draw_y = (x + y) * half_height + offset_draw_y + map_height_px // 2
                pygame.draw.polygon(self.screen, color, [
                    (draw_x, draw_y),
                    (draw_x + half_width, draw_y + half_height),
                    (draw_x, draw_y + 2 * half_height),
                    (draw_x - half_width, draw_y + half_height)
                ])
        for unit in self.units:
            self.draw_unit(int(unit.x), int(unit.y), half_width, half_height, offset_draw_x, offset_draw_y)
        for building in self.buildings:
            self.draw_building(building.x, building.y, half_width, half_height, offset_draw_x, offset_draw_y)
        for res in self.resources:
            self.draw_resource(res.x, res.y, half_width, half_height, offset_draw_x, offset_draw_y)
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

    def draw_unit(self, x, y, half_width, half_height, offset_draw_x, offset_draw_y):
        draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
        draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2
        triangle_points = [
            (draw_x, draw_y - half_height),
            (draw_x - half_width, draw_y + half_height),
            (draw_x + half_width, draw_y + half_height),
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), triangle_points)

    def draw_building(self, x, y, half_width, half_height, offset_draw_x, offset_draw_y):
        draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
        draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2
        size = half_width // 2
        pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))

    def draw_resource(self, x, y, half_width, half_height, offset_draw_x, offset_draw_y):
        draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
        draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2
        radius = half_width // 2
        pygame.draw.circle(self.screen, (255, 255, 255), (draw_x, draw_y), radius)

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

    # === Pop up menu actions and game logic ===

    def move_action(self):
        self.reachable_tiles = set()
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit:
            selected_unit.rest()
            selected_unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()

    def build_action(self):
        self.reachable_tiles = set()
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit and self.selected_tile:
            if self.is_tile_occupied(*self.selected_tile):
                self.message_box.open("There's already a building here.")
                return
            self.popup_menu.open(["Town Centre", "Mill", "Cancel"], {
                "Town Centre": lambda: self.building_selector("town_centre"),
                "Mill": lambda: self.building_selector("mill"),
                "Cancel": self.cancel_action
            })
            self.popup_menu.set_position(
                (SCREEN_WIDTH - self.popup_menu.width) // 2,
                (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
            )
        else:
            self.message_box.open("No unit or tile selected.")
            self.cancel_action()

    def cancel_action(self):
        self.popup_menu.open(self.actions, self.callbacks)
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )

    def gather_action(self):
        self.reachable_tiles = set()
        if self.selected_unit_id is None:
            return
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if not selected_unit:
            return
        unit_pos = (int(selected_unit.x), int(selected_unit.y))
        res = next((r for r in self.resources if (r.x, r.y) == unit_pos), None)
        if not res:
            return
        selected_unit.is_gathering = True
        selected_unit.gather_resource_id = res.id
        if selected_unit:
            selected_unit.rest()
            selected_unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()

    def process_automatic_gathering(self):
        for unit in self.units:
            if getattr(unit, 'is_gathering', False):
                res_id = getattr(unit, 'gather_resource_id', None)
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
                else:
                    unit.is_gathering = False
                    unit.gather_resource_id = None

    def process_enemy_gathering(self):
            for villager in [u for u in self.enemy_units if getattr(u, "type", None) == "villager"]:
                if getattr(villager, "is_gathering", False):
                    res_id = getattr(villager, "gather_resource_id", None)
                    res = next((r for r in self.resources if r.id == res_id), None)
                    if res and (villager.x, villager.y) == (res.x, res.y) and not res.is_depleted():
                        amount_gathered = min(100, res.amount)
                        res.amount -= amount_gathered
                        if res.resource_type == "food":
                            self.enemy_food += amount_gathered
                        elif res.resource_type == "wood":
                            self.enemy_wood += amount_gathered
                        elif res.resource_type == "gold":
                            self.enemy_gold += amount_gathered
                        if res.amount <= 0:
                            villager.is_gathering = False
                            villager.gather_resource_id = None
                    else:
                        villager.is_gathering = False
                        villager.gather_resource_id = None
                    
                    print("food: ", self.enemy_food, "wood: ", self.enemy_wood, "gold: ", self.enemy_gold)

    def undo_action(self):
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if selected_unit and hasattr(selected_unit, "previous_position"):
            selected_unit.x, selected_unit.y = selected_unit.previous_position
        self.reachable_tiles = set()
        if selected_unit:
            selected_unit.selected = False
        self.selected_unit_id = None
        self.popup_menu.close()

    def unit_selection(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        if not selected_building or not isinstance(selected_building, BaseBuildings):
            self.message_box.open("No building selected or wrong type.")
            self.popup_menu.close()
            return
        spawn_x, spawn_y = selected_building.x, selected_building.y
        for unit in self.units:
            if int(unit.x) == spawn_x and int(unit.y) == spawn_y:
                self.message_box.open("Spawn location is blocked.")
                self.popup_menu.close()
                if selected_building:
                    selected_building.selected = False
                self.selected_building_id = None
                return
        building_name = selected_building.type
        if building_name in BUILDINGS:
            b_attr = BUILDINGS[building_name]
        else:
            b_attr = RESOURCE_BUILDINGS[building_name]
        trainable_units = b_attr[6]
        options = trainable_units + ["Cancel"]
        actions = {unit: (lambda u=unit: self.train_action(u, spawn_x, spawn_y)) for unit in trainable_units}
        actions["Cancel"] = self.popup_menu.close
        self.popup_menu.open(options, actions)
        self.popup_menu.set_position(
            (SCREEN_WIDTH - self.popup_menu.width) // 2,
            (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
        )

    def train_action(self, unit_name, spawn_x, spawn_y):
        u_attr = UNITS[unit_name]
        if self.food_amount >= u_attr[1] and self.wood_amount >= u_attr[2] and self.gold_amount >= u_attr[3]:
            new_unit = BaseUnits(spawn_x, spawn_y, u_attr[5], u_attr[6], u_attr[7], u_attr[8], type=unit_name)
            new_unit.unit_queued()
            self.units.append(new_unit)
            self.food_amount -= u_attr[1]
            self.wood_amount -= u_attr[2]
            self.gold_amount -= u_attr[3]
            selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
            if selected_building:
                selected_building.rest()
                selected_building.selected = False
                self.selected_building_id = None
            self.popup_menu.close()
        else:
            self.message_box.open("Insufficient funds")
            selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
            if selected_building:
                selected_building.selected = False
            self.selected_building_id = None
            self.popup_menu.close()

    def research_action(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        self.message_box.open("Researching upgrades")
        if selected_building:
            selected_building.rest()

    def attack_action(self):
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if not selected_unit:
            return

        # Find all enemies in attack range
        if selected_unit.attack_range > 1:
            enemies = self.target_aquisition.all_ranged_enemies(self.selected_tile, selected_unit.attack_range, self.enemy_units)
            enemy_buildings = self.target_aquisition.all_ranged_buildings(self.selected_tile, selected_unit.attack_range, self.e_buildings)
        else:
            enemies = self.target_aquisition.all_adjacent_enemies(self.selected_tile, self.enemy_units)
            enemy_buildings = self.target_aquisition.all_adjacent_buildings(self.selected_tile, self.e_buildings)

        # Combine units and buildings into a single list for cycling.
        targets = []
        for e in enemies:
            targets.append(('unit', e))
        for b in enemy_buildings:
            targets.append(('building', b))

        if not targets:
            self.message_box.open("No enemy in attack range")
            return

        if len(targets) == 1:
            kind, target = targets[0]
            self._execute_attack(selected_unit, target, kind)
        else:
            self.reachable_tiles = set()
            self.popup_menu.close()
            self.target_select_mode = True
            self.targetable_enemies = targets  # Now stores tuples: ('unit'/'building', obj)
            self.selected_target_index = 0
            kind, target = self.targetable_enemies[self.selected_target_index]
            self.selected_tile = (int(target.x), int(target.y))
            self.hovered_tile = self.selected_tile

    def _execute_attack(self, selected_unit, target, kind):
        # kind: 'unit' or 'building'
        if kind == 'unit':
            enemy = target
            damage = ((selected_unit.attack * (1 + BONUS_MULTIPLYER))/enemy.defense) * 25 + FLAT_BONUS
            enemy.health -= damage
            self.enemy_ai.enemy_retaliation(selected_unit, enemy)
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

    def is_tile_occupied(self, x, y):
        return any(b.x == x and b.y == y for b in self.buildings)

    def building_selector(self, building_name):
        if building_name in BUILDINGS:
            b_attr = BUILDINGS[building_name]
        elif building_name in RESOURCE_BUILDINGS:
            b_attr = RESOURCE_BUILDINGS[building_name]
        selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
        if self.food_amount >= b_attr[1] and self.wood_amount >= b_attr[2] and self.gold_amount >= b_attr[3]:
            new_building_id = max([b.id for b in self.buildings], default=0) + 1
            new_building = BaseBuildings(self.selected_tile[0], self.selected_tile[1], b_attr[4], b_attr[5])
            new_building.id = new_building_id
            new_building.type = building_name
            new_building.building_queued()
            self.buildings.append(new_building)
            self.popup_menu.close()
            if selected_unit:
                selected_unit.rest()
                selected_unit.selected = False
            self.food_amount -= b_attr[1]
            self.wood_amount -= b_attr[2]
            self.gold_amount -= b_attr[3]
            self.selected_unit_id = None
        else:
            self.message_box.open("Insufficient funds")
            self.cancel_action()

    def cancel_building_action(self):
        selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
        if selected_building:
            selected_building.selected = False
        self.selected_building_id = None
        self.popup_menu.close()

    def update_VISIBILITY_MAP(self, vision_range):
        for x in range(len(VISIBILITY_MAP)):
            for y in range(len(VISIBILITY_MAP[0])):
                if VISIBILITY_MAP[x][y] == 2:
                    VISIBILITY_MAP[x][y] = 1
        for unit in self.units:
            ux, uy = int(unit.x), int(unit.y)
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx * dx + dy * dy <= vision_range * vision_range:
                        tx = ux + dx
                        ty = uy + dy
                        if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                            VISIBILITY_MAP[tx][ty] = 2
        for building in self.buildings:
            if getattr(building, 'is_constructed', True):
                bx, by = int(building.x), int(building.y)
                for dx in range(-vision_range, vision_range + 1):
                    for dy in range(-vision_range, vision_range + 1):
                        if dx * dx + dy * dy <= vision_range * vision_range:
                            tx = bx + dx
                            ty = by + dy
                            if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                                VISIBILITY_MAP[tx][ty] = 2

    def draw_map_with_fog(self, map_data, color_func, VISIBILITY_MAP, offset_tx=0, offset_ty=0):
        for tx in range(len(map_data)):
            for ty in range(len(map_data[0])):
                draw_tx = tx + offset_tx
                draw_ty = ty + offset_ty
                screen_x = (draw_tx - draw_ty) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
                screen_y = (draw_tx + draw_ty) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y
                if (-self.tile_width <= screen_x <= SCREEN_WIDTH + self.tile_width and
                    -self.tile_height <= screen_y <= SCREEN_HEIGHT + self.tile_height):
                    color = color_func(tx, ty)
                    if VISIBILITY_MAP[tx][ty] == 0:
                        color = (0, 0, 0)
                    elif VISIBILITY_MAP[tx][ty] == 1:
                        color = tuple(c // 2 for c in color)
                    pygame.draw.polygon(self.screen, color, [
                        (screen_x, screen_y),
                        (screen_x + self.tile_width // 2, screen_y + self.tile_height // 2),
                        (screen_x, screen_y + self.tile_height),
                        (screen_x - self.tile_width // 2, screen_y + self.tile_height // 2)
                    ])

    def follow_enemy_camera(self, enemy):
        draw_x = enemy.x + OFFSET_X
        draw_y = enemy.y + OFFSET_Y
        screen_x = (draw_x - draw_y) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
        screen_y = (draw_x + draw_y) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y
        margin = 50
        scroll_speed = 10
        if screen_x < margin:
            self.camera_x += scroll_speed
        elif screen_x > SCREEN_WIDTH - margin:
            self.camera_x -= scroll_speed
        if screen_y < margin:
            self.camera_y += scroll_speed
        elif screen_y > SCREEN_HEIGHT - margin:
            self.camera_y -= scroll_speed

    def end_day(self):
        self.player_turn = False
        for unit in self.units:
            unit.rested()
        for building in self.buildings:
            building.rested()
        self.popup_menu.close()
    
    def run(self):
        if not self.game_over:
            if self.player_turn:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if self.target_select_mode:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_TAB and self.targetable_enemies:
                                # Cycle to next target (unit or building)
                                self.selected_target_index = (self.selected_target_index + 1) % len(self.targetable_enemies)
                                kind, target = self.targetable_enemies[self.selected_target_index]
                                self.selected_tile = (int(target.x), int(target.y))
                                self.hovered_tile = self.selected_tile
                            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                # Attack the currently selected target
                                selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                                kind, target = self.targetable_enemies[self.selected_target_index]
                                self._execute_attack(selected_unit, target, kind)
                            elif event.key == pygame.K_ESCAPE:
                                # Cancel target selection mode
                                self.target_select_mode = False
                                self.targetable_enemies = []
                                self.selected_target_index = 0
                        return
                    if event.type == pygame.KEYDOWN:
                        self.last_key_pressed = event.key

                        if self.message_box.visible:
                            if event.key == pygame.K_RETURN:
                                if self.message_box.ok_button_rect:  # Ensure the OK button exists
                                    self.message_box.close()
                            continue

                        if not self.popup_menu.is_open and not self.is_moving:
                            if event.key == pygame.K_ESCAPE:
                                # Find the currently selected building by its ID
                                self.selected_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
                                if self.selected_unit:
                                    self.selected_unit.selected = False
                                if self.selected_building:
                                    self.selected_building.selected = False
                                self.selected_unit = None
                                self.selected_building_id = None

                            if event.key == pygame.K_1 and self.zoom_level < 1.3:
                                self.zoom_level += 0.1
                            if event.key == pygame.K_2 and self.zoom_level > 0.3:
                                self.zoom_level -= 0.1
                            self.tile_width = int(BASE_TILE_WIDTH * self.zoom_level)
                            self.tile_height = int(BASE_TILE_HEIGHT * self.zoom_level)

                            if event.key == pygame.K_w and self.selected_tile[1] > 0:
                                self.selected_tile = (self.selected_tile[0], self.selected_tile[1] - 1)
                            if event.key == pygame.K_s and self.selected_tile[1] < PLAYABLE_HEIGHT - 1:
                                self.selected_tile = (self.selected_tile[0], self.selected_tile[1] + 1)
                            if event.key == pygame.K_a and self.selected_tile[0] > 0:
                                self.selected_tile = (self.selected_tile[0] - 1, self.selected_tile[1])
                            if event.key == pygame.K_d and self.selected_tile[0] < PLAYABLE_WIDTH - 1:
                                self.selected_tile = (self.selected_tile[0] + 1, self.selected_tile[1])

                            if event.key == pygame.K_TAB:
                                if self.selected_unit_id is not None:
                                    # Find current selected unit's index by its ID
                                    current_index = next((i for i, u in enumerate(self.units) if u.id == self.selected_unit_id), 0)
                                    self.units[current_index].selected = False
                                    next_index = (current_index + 1) % len(self.units)
                                    self.selected_unit = self.units[next_index]
                                else:
                                    self.selected_unit = self.units[0]
                                self.selected_unit.selected = True
                                self.selected_unit_id = self.selected_unit.id
                                self.selected_tile = (int(self.selected_unit.x), int(self.selected_unit.y))
                                friendly_units_for_pathfinding = [u for u in self.units if u != self.selected_unit]
                                path_finding = PathFinding(friendly_units_for_pathfinding, self.enemy_units)
                                self.reachable_tiles = path_finding.bfs_reachable(
                                    (int(self.selected_unit.x), int(self.selected_unit.y)), self.selected_unit.movement_range
                                )

                            if event.key == pygame.K_m:
                                if not self.is_moving:
                                    self.tactical_map_mode = not self.tactical_map_mode

                            if event.key == pygame.K_LSHIFT:
                                unit_found = False
                                for unit in self.units:
                                    if int(unit.x) == self.hovered_tile[0] and int(unit.y) == self.hovered_tile[1]:
                                        if self.selected_unit_id is not None:
                                            prev_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                                            if prev_unit:
                                                prev_unit.selected = False
                                        self.selected_unit = unit
                                        self.selected_unit_id = unit.id
                                        if not self.selected_unit.unit_tired():
                                            self.selected_unit.selected = True
                                            self.selected_tile = (int(self.selected_unit.x), int(self.selected_unit.y))
                                            friendly_units_for_pathfinding = [u for u in self.units if u != self.selected_unit]
                                            path_finding = PathFinding(friendly_units_for_pathfinding, self.enemy_units)
                                            self.reachable_tiles = path_finding.bfs_reachable((int(unit.x), int(unit.y)), unit.movement_range)
                                            unit_found = True

                                            # Deselect any building if a unit is selected
                                            if self.selected_building_id is not None:
                                                prev_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
                                                if prev_building:
                                                    prev_building.selected = False
                                            self.selected_building_id = None
                                        break

                                if not unit_found:
                                    building_found = False
                                    for building in self.buildings:
                                        if int(building.x) == self.hovered_tile[0] and int(building.y) == self.hovered_tile[1]:
                                            if self.selected_building_id is not None:
                                                prev_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
                                                if prev_building:
                                                    prev_building.selected = False
                                            self.selected_building_id = building.id
                                            print("Selected building id:", self.selected_building_id)
                                            print("Selected building action count:", building.action_count)
                                            if self.selected_unit_id is not None:
                                                prev_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                                                if prev_unit:
                                                    prev_unit.selected = False
                                                self.selected_unit_id = None
                                                self.selected_unit = None
                                                self.reachable_tiles = []
                                            if not building.building_tired():
                                                building.selected = True
                                                building_found = True
                                                building_name = building.type
                                                if building_name in BUILDINGS:
                                                    building_actions = ["Train", "Research", "Cancel"]
                                                    building_callbacks = {
                                                        "Train": self.unit_selection,
                                                        "Research": self.research_action,
                                                        "Cancel": self.cancel_building_action
                                                    }
                                                else:
                                                    building_actions = ["Research", "Cancel"]
                                                    building_callbacks = {
                                                        "Research": self.research_action,
                                                        "Cancel": self.cancel_building_action
                                                    }
                                                self.popup_menu.open(building_actions, building_callbacks)
                                                self.popup_menu.set_position(
                                                    (SCREEN_WIDTH - self.popup_menu.width) // 2,
                                                    (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
                                                )

                                if not unit_found and not building_found:
                                    if self.selected_unit_id is not None:
                                        prev_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                                        if prev_unit:
                                            prev_unit.selected = False
                                        self.selected_unit_id = None
                                        self.selected_unit = None
                                        self.reachable_tiles = []
                                    if self.selected_building_id is not None:
                                        prev_building = next((b for b in self.buildings if b.id == self.selected_building_id), None)
                                        if prev_building:
                                            prev_building.selected = False
                                        self.selected_building_id = None

                                    self.popup_menu.open(["End Day"], {"End Day": self.end_day})
                                    self.popup_menu.menu_type = "options"
                                    self.popup_menu.set_position(
                                        (SCREEN_WIDTH - self.popup_menu.width) // 2,
                                        (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
                                    )

                            if event.key == pygame.K_SPACE and self.selected_unit_id is not None:
                                # Find the unit object by its ID
                                self.selected_unit = next((u for u in self.units if u.id == self.selected_unit_id), None)
                                if self.selected_unit:
                                    # New PathFinding instance for this unit
                                    friendly_units_for_pathfinding = [u for u in self.units if u != self.selected_unit]
                                    path_finding = PathFinding(friendly_units_for_pathfinding, self.enemy_units)
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
                                            else:
                                                self.message_box.open("No valid path within movement range")
                                    self.tactical_map_mode = False

                        if self.popup_menu.is_open:
                            if event.key == pygame.K_w:
                                self.popup_menu.move_selection(-1)
                            elif event.key == pygame.K_s:
                                self.popup_menu.move_selection(1)
                            elif event.key == pygame.K_RETURN:
                                choice = self.popup_menu.select()
                            elif event.key == pygame.K_ESCAPE and getattr(self.popup_menu, "menu_type", None) == "options":
                                self.popup_menu.close()
                                continue
            else:
                # --- Only plan once at start of enemy turn ---
                if not self.enemy_paths_planned:
                    self.enemy_ai.plan_enemy_paths(self.enemy_units, self.units, self.buildings, self.resources)
                    self.enemy_paths_planned = True
                    self.enemy_turn_index = 0
                    self.enemy_turn_phase = 'move'
                    self.enemy_turn_delay = 0

                # --- If all enemies processed, end turn ---
                if self.enemy_turn_index >= len(self.enemy_units):
                    self.player_turn = True
                    self.enemy_paths_planned = False
                    self.process_automatic_gathering()
                    self.process_enemy_gathering()
                    return

                enemy = self.enemy_units[self.enemy_turn_index]
                # Delay between actions for clarity/animation (e.g. 15 frames = 0.25s at 60 FPS)
                if self.enemy_turn_delay > 0:
                    self.enemy_turn_delay -= 1
                    return

                if self.enemy_turn_phase == 'move':
                    # Animate movement
                    if enemy.path:
                        enemy.move_along_path(self.enemy_units)
                        self.follow_enemy_camera(enemy)
                        # Only move one tile per frame or step (for clarity/animation)
                        self.enemy_turn_delay = 0  # Adjust as needed for your game speed
                        if not enemy.path:
                            self.enemy_turn_phase = 'attack'
                    else:
                        self.enemy_turn_phase = 'attack'

                elif self.enemy_turn_phase == 'attack':
                    # Try to attack player unit/building
                    did_attack = False
                    # Units
                    for player in self.units:
                        if player.health > 0 and abs(enemy.x - player.x) + abs(enemy.y - player.y) == 1:
                            damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/player.defense) * 25 + FLAT_BONUS
                            player.health -= damage
                            self.enemy_ai.enemy_retaliation(enemy, player)
                            print("enemy:", enemy.health)
                            print("player:", player.health)
                            did_attack = True
                            break
                    # Buildings
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

        # Check health of units and buildings.
        for unit in self.units:
            if unit.health <= 0:
                print(f"Player at ({unit.x},{unit.y}) is defeated!")
                self.units.remove(unit)
        for building in self.buildings:
            if building.hitpoints <= 0:
                print(f"Building at ({building.x},{building.y}) is destroyed!")
                self.buildings.remove(building)
        for enemy in self.enemy_units:
            if enemy.health <= 0:
                self.enemy_units.remove(enemy)
                print(enemy, "died")
        for eb in self.e_buildings:
            if eb.hitpoints <= 0:
                print(f"Building at ({building.x},{building.y}) is destroyed!")
                self.e_buildings.remove(eb)

        self.hovered_tile = self.selected_tile

        # Convert hovered tile to screen coordinates
        draw_x = self.hovered_tile[0] + OFFSET_X
        draw_y = self.hovered_tile[1] + OFFSET_Y
        screen_x = (draw_x - draw_y) * self.tile_width // 2 + (SCREEN_WIDTH // 2) + self.camera_x
        screen_y = (draw_x + draw_y) * self.tile_height // 2 + (SCREEN_HEIGHT // 4) + self.camera_y

        # Scroll if tile is near screen edges
        margin = 50  # pixels from screen edge to trigger camera move
        scroll_speed = 10

        if screen_x < margin:
            self.camera_x += scroll_speed
        elif screen_x > SCREEN_WIDTH - margin:
            self.camera_x -= scroll_speed

        if screen_y < margin:
            self.camera_y += scroll_speed
        elif screen_y > SCREEN_HEIGHT - margin:
            self.camera_y -= scroll_speed

        if self.is_moving:
            self.selected_unit.move_along_path(self.enemy_units)
            # --- Stop gathering if the unit moves off the resource tile during movement ---
            if getattr(self.selected_unit, "is_gathering", False):
                res_id = getattr(self.selected_unit, "gather_resource_id", None)
                res = next((r for r in self.resources if r.id == res_id), None)
                if not res or (int(self.selected_unit.x), int(self.selected_unit.y)) != (res.x, res.y):
                    self.selected_unit.is_gathering = False
                    self.selected_unit.gather_resource_id = None
                    
            if not self.selected_unit.path:
                self.is_moving = False

                actions = ["Move", "Build", "Undo Move"]
                callbacks = {
                    "Move": self.move_action,
                    "Build": self.build_action,
                    "Undo Move": self.undo_action
                }

                # Check if unit landed on a resource tile
                landed_tile = (int(self.selected_unit.x), int(self.selected_unit.y))
                for res in self.resources:
                    if (res.x, res.y) == landed_tile:
                        actions.insert(2, "Gather")  # Insert Gather before Undo
                        callbacks["Gather"] = self.gather_action
                        break

                # NEW ARCHER LOGIC
                if hasattr(self.selected_unit, "attack_range") and self.selected_unit.attack_range > 1:
                    if self.target_aquisition.any_ranged_enemy_in_range(self.selected_tile, self.selected_unit.attack_range, self.enemy_units):
                        actions.insert(0, "Attack")
                        callbacks["Attack"] = self.attack_action
                else:
                    if self.target_aquisition.is_enemy_adjacent(self.selected_tile, self.enemy_units):
                        actions.insert(0, "Attack")
                        callbacks["Attack"] = self.attack_action
                        
                self.popup_menu.open(actions, callbacks)
                self.popup_menu.set_position(
                    (SCREEN_WIDTH - self.popup_menu.width) // 2,
                    (SCREEN_HEIGHT - (self.popup_menu.item_height * len(self.popup_menu.options))) // 2
                )

        if self.tactical_map_mode:
            self.draw_tactical_map()
            self.clock.tick(30)
            return

        self.update_VISIBILITY_MAP(vision_range=3)

        self.screen.fill((32, 32, 32))

        self.draw_map_with_fog(
            PLAYABLE_MAP,
            lambda tx, ty: (
                (34, 177, 76) if PLAYABLE_MAP[tx][ty] == "G" else
                (0, 162, 232) if PLAYABLE_MAP[tx][ty] == "W" else
                (127, 127, 127)
            ),VISIBILITY_MAP, OFFSET_X, OFFSET_Y
        )

        # Only draw reachable tiles if a unit is selected
        if self.selected_unit:
            for tile in (self.reachable_tiles or []):
                self.draw_tile_highlight(tile[0], tile[1], (0, 255, 255, 90))

        # Drawing
        for resource in self.resources:
            resource.draw(self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y, self.tile_width, self.tile_height, self.resources)
        for building in self.buildings:
            building.draw(self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y, self.tile_width, self.tile_height)
        for eb in self.e_buildings:
            ex, ey = int(eb.x), int(eb.y)
            if (
                0 <= ex < len(VISIBILITY_MAP)
                and 0 <= ey < len(VISIBILITY_MAP[0])
                and VISIBILITY_MAP[ex][ey] == 2
            ):
                eb.draw(self.screen, OFFSET_X, OFFSET_Y, self.camera_x, self.camera_y, self.tile_width, self.tile_height)
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

        if self.hovered_tile:
            self.draw_tile_highlight_crimson(*self.hovered_tile, (220, 20, 60))  # crimson outline

        if self.selected_tile:
            self.draw_tile_highlight_crimson(*self.selected_tile, (220, 20, 60))  # crimson outline

        # === RESOURCE AND POPULATION DISPLAY BAR === #
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
