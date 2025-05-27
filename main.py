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

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Empires PSP")

zoom_level = 1

clock = pygame.time.Clock()

# Selection state
selected_tile = (4, 4)
hovered_tile = selected_tile  # Hovered tile now follows selected tile
path = []
is_moving = False

# Tactical map mode flag
tactical_map_mode = False
last_key_pressed = None

# Initialize reachable_tiles before the main loop
reachable_tiles = set()

# === RESOURCE AND POPULATION TRACKING === #
food_amount = 500
wood_amount = 500
gold_amount = 500

selected_unit = None
selected_building = None
is_moving = False
running = True

# Object initialization
villagers = [
    BaseUnits(5, 5, 5, 50, 25)
]
town_centre = BaseBuildings(3, 3, 500, 10)
town_centre.is_constructed = True

resource = [
    ResourceSource(1, 3, "food", 500),
    ResourceSource(3, 1, "gold", 5000),
    ResourceSource(5, 3, "wood", 400)
]

spearmen = BaseUnits(7, 7, 7, 100, 100)

units = villagers
buildings = [town_centre]
resources = resource
population = len(units)
enemy_units = [spearmen]

player_turn = True

message_box = MessageBox(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
popup_menu = PopupMenu([], {}, 10, 10)
path_finding = PathFinding(enemy_units)
target_aquisition = TargetAquisition()
enemy_ai = EnemyAi(enemy_units)
enemy_moving = False  # Flag to track if enemies are animating/moving
enemy_paths_planned = False  # Flag to avoid re-planning paths every frame

game_over = False

# Tactical map
def draw_tactical_map():
    screen.fill((32, 32, 32))  # Fill screen with black (clear previous frame)
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
                color = (0, 0, 0)  # Unseen tiles are black
            else:
                color = (34, 177, 76) if tile == "G" else (127, 127, 127) if tile == "S" else (0, 162, 232)

            draw_x = (x - y) * half_width + offset_draw_x + map_width_px // 2
            draw_y = (x + y) * half_height + offset_draw_y + map_height_px // 2
            pygame.draw.polygon(screen, color, [
                (draw_x, draw_y),
                (draw_x + half_width, draw_y + half_height),
                (draw_x, draw_y + 2 * half_height),
                (draw_x - half_width, draw_y + half_height)
            ])

    # Loop through units, buildings, and resources and draw them
    for unit in units:
        draw_unit(int(unit.x), int(unit.y), half_width, half_height, offset_draw_x, offset_draw_y)

    for building in buildings:
        draw_building(building.x, building.y, half_width, half_height, offset_draw_x, offset_draw_y)

    for res in resources:
        draw_resource(res.x, res.y, half_width, half_height, offset_draw_x, offset_draw_y)

    # Draw camera view (isometric polygon)
    corners = [
        (0, 0),
        (SCREEN_WIDTH, 0),
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        (0, SCREEN_HEIGHT)
    ]
    iso_points = []
    for sx, sy in corners:
        world_x = (sx - SCREEN_WIDTH // 2) - CAMERA_X  # Invert for tactical view
        world_y = (sy - SCREEN_HEIGHT // 4) - CAMERA_Y

        tile_y = ((2 * world_y - world_x) // TILE_HEIGHT) // 2
        tile_x = ((2 * world_y + world_x) // TILE_HEIGHT) // 2

        draw_x = (tile_x - tile_y) * half_width + offset_draw_x + map_width_px // 2
        draw_y = (tile_x + tile_y) * half_height + offset_draw_y + map_height_px // 2
        iso_points.append((draw_x, draw_y))

    pygame.draw.polygon(screen, (255, 255, 0), iso_points, 2)
    pygame.display.flip()

# Draw units, buildings and resources on tactical map
def draw_unit(x, y, half_width, half_height, offset_draw_x, offset_draw_y):
    draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
    draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2

    triangle_points = [
        (draw_x, draw_y - half_height),
        (draw_x - half_width, draw_y + half_height),
        (draw_x + half_width, draw_y + half_height),
    ]
    pygame.draw.polygon(screen, (255, 255, 255), triangle_points)

def draw_building(x, y, half_width, half_height, offset_draw_x, offset_draw_y):
    draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
    draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2

    size = half_width // 2
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))

def draw_resource(x, y, half_width, half_height, offset_draw_x, offset_draw_y):
    draw_x = (x - y) * half_width + offset_draw_x + (PLAYABLE_WIDTH * half_width)
    draw_y = (x + y) * half_height + offset_draw_y + (PLAYABLE_HEIGHT * half_height) // 2

    radius = half_width // 2
    pygame.draw.circle(screen, (255, 255, 255), (draw_x, draw_y), radius)

# Tile highlight drawing

def draw_tile_highlight(tx, ty, color, alpha=128):
    draw_tx = tx + OFFSET_X
    draw_ty = ty + OFFSET_Y
    screen_x = (draw_tx - draw_ty) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + CAMERA_X
    screen_y = (draw_tx + draw_ty) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + CAMERA_Y

    overlay = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(overlay, color, [
        (TILE_WIDTH // 2, 0),
        (TILE_WIDTH, TILE_HEIGHT // 2),
        (TILE_WIDTH // 2, TILE_HEIGHT),
        (0, TILE_HEIGHT // 2)
    ])
    screen.blit(overlay, (screen_x - TILE_WIDTH // 2, screen_y))

# Pop up menu actions

def move_action():
    global reachable_tiles, selected_unit
    reachable_tiles = set()  # Clear the reachable tiles
    if selected_unit:
        selected_unit.rest()
        selected_unit.selected = False  # Deselect the unit
    selected_unit = None  # Clear the selected unit
    popup_menu.close()

def build_action():
    global buildings, reachable_tiles
    reachable_tiles = set()  # Clear the reachable tiles
    if selected_unit and selected_tile:
        if is_tile_occupied(*selected_tile):
            message_box.open("There's already a building here.")
            return
        popup_menu.open(["Town Centre", "Mill", "Cancel"], {
                    "Town Centre": build_town_centre,
                    "Mill": build_mill,
                    "Cancel": cancel_action
        })
        popup_menu.set_position(
            (SCREEN_WIDTH - popup_menu.width) // 2,
            (SCREEN_HEIGHT - (popup_menu.item_height * len(popup_menu.options))) // 2
        )

def cancel_action():
    popup_menu.open(actions, callbacks)
    popup_menu.set_position(
        (SCREEN_WIDTH - popup_menu.width) // 2,
        (SCREEN_HEIGHT - (popup_menu.item_height * len(popup_menu.options))) // 2
    )


def gather_action():
    global reachable_tiles, selected_unit, resources, food_amount, wood_amount, gold_amount
    if not selected_unit:
        return

    unit_pos = (int(selected_unit.x), int(selected_unit.y))
    for res in resources:
        if (res.x, res.y) == unit_pos:
            amount_gathered = min(100, res.amount)
            res.amount -= amount_gathered
            reachable_tiles = set()  # Clear the reachable tiles
            if selected_unit:
                selected_unit.selected = False  # Deselect the unit
            selected_unit = None  # Clear the selected unit
            popup_menu.close()

            if res.resource_type == "food":
                    food_amount += amount_gathered
            elif res.resource_type == "wood":
                wood_amount += amount_gathered
            elif res.resource_type == "gold":
                gold_amount += amount_gathered

            # Remove the resource if depleted
            if res.amount <= 0:
                resources.remove(res)
                message_box.open(f"{res.resource_type} has been depleted.")
                popup_menu.close()
            break

def undo_action():
    global reachable_tiles, selected_unit
    if selected_unit and hasattr(selected_unit, "previous_position"):
        selected_unit.x, selected_unit.y = selected_unit.previous_position
        popup_menu.close()
    reachable_tiles = set()  # Clear the reachable tiles
    if selected_unit:
        selected_unit.selected = False  # Deselect the unit
    selected_unit = None  # Clear the selected unit

def train_action():
    global population, villagers, units, selected_building, food_amount

    if not selected_building or not isinstance(selected_building, BaseBuildings):
        message_box.open("No building selected or wrong type.")
        popup_menu.close()
        return

    # Determine spawn position (e.g., adjacent tile)
    spawn_x, spawn_y = selected_building.x, selected_building.y

    # Optionally check that tile is not blocked
    for unit in units:
        if int(unit.x) == spawn_x and int(unit.y) == spawn_y:
            message_box.open("Spawn location is blocked.")
            popup_menu.close()
            return
    
    # Create new villager
    if food_amount >= 50:
        new_villager = BaseUnits(spawn_x, spawn_y, 5, 50, 25)
        villagers.append(new_villager)
        food_amount -= 50
        selected_building.rest()
        print(selected_building.action_count)
    else:
        message_box.open("insufficient funds")
        cancel_action()

    popup_menu.close()

def research_action():
    message_box.open("Researching upgrades")
    selected_building.rest()

def attack_action():
    global reachable_tiles, selected_unit

    damage = 0
    bonus_multiplier = 0
    flat_bonus = 0

    enemy = target_aquisition.adjacent_enemy(selected_tile, enemy_units)
    damage = ((selected_unit.attack * (1 + bonus_multiplier))/enemy.defense) * 25 + flat_bonus
    enemy.health -= damage
    print("enemy:", enemy.health)
    print("player:", selected_unit.health)
    selected_unit.rest()
    reachable_tiles = set()  # Clear the reachable tiles

    if enemy.health <= 0:
        enemy_units.remove(enemy)
        print(enemy, "died")
        popup_menu.close()

    if selected_unit.health <= 0:
        units.remove(selected_unit)
        print(selected_unit, "died")
        popup_menu.close()


    if selected_unit:
        selected_unit.selected = False  # Deselect the unit
    selected_unit = None  # Clear the selected unit
    popup_menu.close()


# Buildings

tile_building = False

def is_tile_occupied(x, y):
    return any(b.x == x and b.y == y for b in buildings)

def build_town_centre():
    global buildings, wood_amount, gold_amount, max_pop
    if selected_unit and selected_tile:
        if is_tile_occupied(*selected_tile):
            message_box.open("There's already a building here.")
            return
        if wood_amount >= 400 and gold_amount >= 400:
            new_building = BaseBuildings(selected_tile[0], selected_tile[1], 500, 10)
            new_building.is_constructed = True
            buildings.append(new_building)
            popup_menu.close()
            selected_unit.rest()
            wood_amount -= 400
            gold_amount -= 400
            max_pop += 10
        else:
            message_box.open("Insufficient funds")
            cancel_action()

def build_mill():
    global buildings, wood_amount
    if selected_unit and selected_tile:
        if is_tile_occupied(*selected_tile):
            message_box.open("There's already a building here.")
            return
        if wood_amount >= 50:
            new_building = BaseBuildings(selected_tile[0], selected_tile[1], 200, 0)
            new_building.is_constructed = True
            buildings.append(new_building)
            popup_menu.close()
            selected_unit.rest()
            wood_amount -= 50
        else:
            message_box.open("Insufficient funds")
            cancel_action()

def cancel_building_action():
    global selected_building
    if selected_building:
        selected_building.selected = False
    selected_building = None
    popup_menu.close()

def update_VISIBILITY_MAP(units, buildings, VISIBILITY_MAP, vision_range):
    # Decay all visibility to 1 (seen before but not currently visible)
    for x in range(len(VISIBILITY_MAP)):
        for y in range(len(VISIBILITY_MAP[0])):
            if VISIBILITY_MAP[x][y] == 2:
                VISIBILITY_MAP[x][y] = 1

    # Apply current unit vision (set to 2)
    for unit in units:
        ux, uy = int(unit.x), int(unit.y)
        for dx in range(-vision_range, vision_range + 1):
            for dy in range(-vision_range, vision_range + 1):
                if dx * dx + dy * dy <= vision_range * vision_range:
                    tx = ux + dx
                    ty = uy + dy
                    if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                        VISIBILITY_MAP[tx][ty] = 2

    for building in buildings:
        if getattr(building, 'is_constructed', True):
            bx, by = int(building.x), int(building.y)
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx * dx + dy * dy <= vision_range * vision_range:
                        tx = bx + dx
                        ty = by + dy
                        if 0 <= tx < len(VISIBILITY_MAP) and 0 <= ty < len(VISIBILITY_MAP[0]):
                            VISIBILITY_MAP[tx][ty] = 2


def draw_map_with_fog(map_data, color_func, VISIBILITY_MAP, offset_tx=0, offset_ty=0):
    for tx in range(len(map_data)):
        for ty in range(len(map_data[0])):
            draw_tx = tx + offset_tx
            draw_ty = ty + offset_ty
            screen_x = (draw_tx - draw_ty) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + CAMERA_X
            screen_y = (draw_tx + draw_ty) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + CAMERA_Y
            if (-TILE_WIDTH <= screen_x <= SCREEN_WIDTH + TILE_WIDTH and
                -TILE_HEIGHT <= screen_y <= SCREEN_HEIGHT + TILE_HEIGHT):

                # Get base tile color
                color = color_func(tx, ty)

                # Handle visibility
                if VISIBILITY_MAP[tx][ty] == 0:
                    # Fully unseen: draw black
                    color = (0, 0, 0)
                elif VISIBILITY_MAP[tx][ty] == 1:
                    # Previously seen but not currently visible: dim
                    color = tuple(c // 2 for c in color)

                # Draw the tile
                pygame.draw.polygon(screen, color, [
                    (screen_x, screen_y),
                    (screen_x + TILE_WIDTH // 2, screen_y + TILE_HEIGHT // 2),
                    (screen_x, screen_y + TILE_HEIGHT),
                    (screen_x - TILE_WIDTH // 2, screen_y + TILE_HEIGHT // 2)
                ])

    # Draw enemy units only on visible tiles
    for enemy in enemy_units:
        ex, ey = int(enemy.x), int(enemy.y)  # Enemy coordinates in the tile grid
        if VISIBILITY_MAP[ex][ey] == 2:  # Only render if tile is fully visible
            enemy.draw(screen, OFFSET_X, OFFSET_Y, CAMERA_X, CAMERA_Y, TILE_WIDTH, TILE_HEIGHT)

def follow_enemy_camera(enemy):
    global CAMERA_X, CAMERA_Y
    # Use same math as you do for selected tiles
    draw_x = enemy.x + OFFSET_X
    draw_y = enemy.y + OFFSET_Y
    screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + CAMERA_X
    screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + CAMERA_Y

    margin = 50
    scroll_speed = 10

    if screen_x < margin:
        CAMERA_X += scroll_speed
    elif screen_x > SCREEN_WIDTH - margin:
        CAMERA_X -= scroll_speed

    if screen_y < margin:
        CAMERA_Y += scroll_speed
    elif screen_y > SCREEN_HEIGHT - margin:
        CAMERA_Y -= scroll_speed

def end_day():
    global player_turn
    player_turn = False
    for unit in units:
        unit.rested()
    for building in buildings:
        building.rested()
    popup_menu.close()

# === MAIN LOOP === #

while running:
    if not game_over:
        if player_turn:
            for event in pygame.event.get():
                if not is_moving:
                    tactical_map_queued = False
                    last_tactical_key = None

                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    last_key_pressed = event.key

                    if message_box.visible:
                        if event.key == pygame.K_RETURN:
                            if message_box.ok_button_rect:  # Ensure the OK button exists
                                message_box.close()
                        continue

                    if not popup_menu.is_open and not is_moving:
                        if event.key == pygame.K_ESCAPE:
                            if selected_unit:
                                selected_unit.selected = False
                            if selected_building:
                                selected_building.selected = False
                            selected_unit = None
                            selected_building = None

                        if event.key == pygame.K_1 and zoom_level < 1.3:
                            zoom_level += 0.1
                        if event.key == pygame.K_2 and zoom_level > 0.3:
                            zoom_level -= 0.1
                        TILE_WIDTH = int(BASE_TILE_WIDTH * zoom_level)
                        TILE_HEIGHT = int(BASE_TILE_HEIGHT * zoom_level)

                        if event.key == pygame.K_w and selected_tile[1] > 0:
                            selected_tile = (selected_tile[0], selected_tile[1] - 1)
                        if event.key == pygame.K_s and selected_tile[1] < PLAYABLE_HEIGHT - 1:
                            selected_tile = (selected_tile[0], selected_tile[1] + 1)
                        if event.key == pygame.K_a and selected_tile[0] > 0:
                            selected_tile = (selected_tile[0] - 1, selected_tile[1])
                        if event.key == pygame.K_d and selected_tile[0] < PLAYABLE_WIDTH - 1:
                            selected_tile = (selected_tile[0] + 1, selected_tile[1])

                        if event.key == pygame.K_TAB:
                            if selected_unit:
                                selected_unit.selected = False
                                current_index = units.index(selected_unit)
                                next_index = (current_index + 1) % len(units)
                                selected_unit = units[next_index]
                            else:
                                selected_unit = units[0]
                            selected_unit.selected = True
                            selected_tile = (int(selected_unit.x), int(selected_unit.y))
                            reachable_tiles = path_finding.bfs_reachable((int(selected_unit.x), int(selected_unit.y)), selected_unit.movement_range)

                        if event.key == pygame.K_m:
                            if not is_moving:
                                tactical_map_mode = not tactical_map_mode
                            else:
                                tactical_map_queued = True
                                last_tactical_key = "m"

                        if event.key == pygame.K_LSHIFT:
                            unit_found = False
                            for unit in units:
                                if int(unit.x) == hovered_tile[0] and int(unit.y) == hovered_tile[1]:
                                    if selected_unit:
                                        selected_unit.selected = False
                                    selected_unit = unit
                                    if selected_unit.unit_tired() == False:
                                        selected_unit.selected = True
                                        selected_tile = (int(selected_unit.x), int(selected_unit.y))
                                        reachable_tiles = path_finding.bfs_reachable((int(unit.x), int(unit.y)), unit.movement_range)
                                        unit_found = True

                                        # Deselect any building if a unit is selected
                                        if selected_building:
                                            selected_building.selected = False
                                            selected_building = None
                                        break

                            if not unit_found:
                                building_found = False
                                for building in buildings:
                                    if building.x == hovered_tile[0] and building.y == hovered_tile[1]:
                                        if selected_building:
                                            selected_building.selected = False
                                        selected_building = building
                                        if selected_building.building_tired() == False:
                                            selected_building.selected = True
                                            building_found = True

                                            if selected_unit:
                                                selected_unit.selected = False
                                                selected_unit = None
                                                reachable_tiles = []

                                            popup_menu.open(["Train", "Research", "Cancel"], {
                                                "Train": train_action,
                                                "Research": research_action,
                                                "Cancel": cancel_building_action
                                            })
                                            popup_menu.set_position(
                                                (SCREEN_WIDTH - popup_menu.width) // 2,
                                                (SCREEN_HEIGHT - (popup_menu.item_height * len(popup_menu.options))) // 2
                                            )

                                            break

                            if not unit_found and not building_found:
                                if selected_unit:
                                    selected_unit.selected = False
                                    selected_unit = None
                                    reachable_tiles = []
                                if selected_building:
                                    selected_building.selected = False
                                    selected_building = None

                                popup_menu.open(["End Day"], {"End Day": end_day})
                                popup_menu.set_position(
                                            (SCREEN_WIDTH - popup_menu.width) // 2,
                                            (SCREEN_HEIGHT - (popup_menu.item_height * len(popup_menu.options))) // 2
                                        )

                        if event.key == pygame.K_SPACE and selected_unit:
                            tactical_map_mode = False
                            if selected_tile in reachable_tiles:
                                selected_unit.previous_position = (selected_unit.x, selected_unit.y)
                                start_pos = (int(selected_unit.x), int(selected_unit.y))

                                if selected_tile == start_pos:
                                    selected_unit.path = [(float(selected_unit.x), float(selected_unit.y))]
                                    is_moving = True
                                else:
                                    path = path_finding.a_star(start_pos, selected_tile, selected_unit.movement_range)
                                    if path:
                                        selected_unit.path = [(float(x), float(y)) for x, y in path]
                                        is_moving = True
                                    else:
                                        message_box.open("No valid path within movement range")
                            tactical_map_mode = False

                    if popup_menu.is_open:
                        if event.key == pygame.K_w:
                            popup_menu.move_selection(-1)
                        elif event.key == pygame.K_s:
                            popup_menu.move_selection(1)
                        elif event.key == pygame.K_RETURN:
                            choice = popup_menu.select()
        else:
            # ENEMY TURN PHASE
            if not enemy_paths_planned:
                enemy_ai.plan_enemy_paths(enemy_units, units, buildings)
                enemy_paths_planned = True
                enemy_moving = True

            # Animate enemy movement
            all_paths_empty = True
            for enemy in enemy_units:
                enemy.move_along_path(enemy_units)
                if enemy.path:  # If any enemy still moving, don't end turn yet
                    all_paths_empty = False

            if enemy_moving and all_paths_empty:
                # After all movement, handle attacks for adjacent enemies
                enemy_ai.try_enemy_attack(enemy_units, units, buildings)
                # End the enemy turn, switch back to player
                player_turn = True
                enemy_moving = False
                enemy_paths_planned = False

            # Find a visible enemy that is moving (has a path)
            enemy_to_follow = None
            for enemy in enemy_units:
                ex, ey = int(enemy.x), int(enemy.y)
                if VISIBILITY_MAP[ex][ey] == 2 and enemy.path:
                    enemy_to_follow = enemy
                    break

            # Call the camera-follow if found
            if enemy_to_follow:
                follow_enemy_camera(enemy_to_follow)
        
    for enemy in enemy_units:
        print(f"Enemy at ({enemy.x}, {enemy.y}) path: {enemy.path}")

    if is_moving and not selected_unit.path:
        is_moving = False
        if tactical_map_queued and last_tactical_key == "m":
            tactical_map_mode = not tactical_map_mode
        tactical_map_queued = False
        last_tactical_key = None

    hovered_tile = selected_tile

    # Convert hovered tile to screen coordinates
    draw_x = hovered_tile[0] + OFFSET_X
    draw_y = hovered_tile[1] + OFFSET_Y
    screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + CAMERA_X
    screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + CAMERA_Y

    # Scroll if tile is near screen edges
    margin = 50  # pixels from screen edge to trigger camera move
    scroll_speed = 10

    if screen_x < margin:
        CAMERA_X += scroll_speed
    elif screen_x > SCREEN_WIDTH - margin:
        CAMERA_X -= scroll_speed

    if screen_y < margin:
        CAMERA_Y += scroll_speed
    elif screen_y > SCREEN_HEIGHT - margin:
        CAMERA_Y -= scroll_speed

    if is_moving:
        selected_unit.move_along_path(enemy_units)
        if not selected_unit.path:
            is_moving = False

            actions = ["Move", "Build", "Undo Move"]
            callbacks = {
                "Move": move_action,
                "Build": build_action,
                "Undo Move": undo_action
            }

            # Check if unit landed on a resource tile
            landed_tile = (int(selected_unit.x), int(selected_unit.y))
            for res in resources:
                if (res.x, res.y) == landed_tile:
                    actions.insert(2, "Gather")  # Insert Gather before Undo
                    callbacks["Gather"] = gather_action
                    break
            
            popup_menu.open(actions, callbacks)
            popup_menu.set_position(
                (SCREEN_WIDTH - popup_menu.width) // 2,
                (SCREEN_HEIGHT - (popup_menu.item_height * len(popup_menu.options))) // 2
            )

            if target_aquisition.is_enemy_adjacent(selected_tile, enemy_units):
                actions.insert(0, "Attack")
                callbacks["Attack"] = attack_action

    if tactical_map_mode:
        draw_tactical_map()
        clock.tick(30)
        continue

    update_VISIBILITY_MAP(units, buildings, VISIBILITY_MAP, vision_range=3)

    screen.fill((32, 32, 32))

    draw_map_with_fog(
        PLAYABLE_MAP,
        lambda tx, ty: (
            (34, 177, 76) if PLAYABLE_MAP[tx][ty] == "G" else
            (0, 162, 232) if PLAYABLE_MAP[tx][ty] == "W" else
            (127, 127, 127)
        ),
        VISIBILITY_MAP,
        OFFSET_X,
        OFFSET_Y
    )

    # Only draw reachable tiles if a unit is selected
    if selected_unit:
        for tile in reachable_tiles:
            draw_tile_highlight(tile[0], tile[1], (0, 255, 255, 90))

    if hovered_tile:
        draw_tile_highlight(*hovered_tile, (255, 255, 255, 60))
    if selected_tile:
        draw_tile_highlight(*selected_tile, (255, 255, 0, 100))

    for building in buildings:
        building.draw(screen, OFFSET_X, OFFSET_Y, CAMERA_X, CAMERA_Y, TILE_WIDTH, TILE_HEIGHT)
    for resource in resources:
        resource.draw(screen, OFFSET_X, OFFSET_Y, CAMERA_X, CAMERA_Y, TILE_WIDTH, TILE_HEIGHT, resources)
    for unit in units:
        unit.draw(screen, OFFSET_X, OFFSET_Y, CAMERA_X, CAMERA_Y, TILE_WIDTH, TILE_HEIGHT)

    # === RESOURCE AND POPULATION DISPLAY BAR === #
    bar_height = 25
    bar_color = (20, 20, 20)
    text_color = (255, 255, 255)
    font = pygame.font.SysFont(None, 24)

    # Fill top bar background
    pygame.draw.rect(screen, bar_color, (0, 0, SCREEN_WIDTH, bar_height))

    # Population
    population = len(units)
    max_pop = 0  # Reset before accumulation
    for building in buildings:
        if building.is_constructed:
            max_pop += building.population_limit

    # Resource display
    resource_text = (
        f"| Food: {food_amount} "
        f"| Wood: {wood_amount} "
        f"| Gold: {gold_amount} "
        f"| Pop: {population} / {max_pop} |"
    )
    text_surface = font.render(resource_text, True, text_color)

    # Calculate the x-coordinate to center the text horizontally
    text_width = text_surface.get_width()
    center_x = (SCREEN_WIDTH - text_width) // 2

    # Calculate the y-coordinate to center the text vertically
    center_y = (bar_height - text_surface.get_height()) // 2

    # Draw the text centered in the display bar
    screen.blit(text_surface, (center_x, center_y))

    popup_menu.draw(screen)
    message_box.draw()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
