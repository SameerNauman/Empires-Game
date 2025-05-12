import pygame
import random
import heapq
from collections import deque

# Initialize pygame
pygame.init()
screen_width, screen_height = 480, 272
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Empires PSP")

# Define tile types and costs
tile_types = {"G": 1, "S": 3, "W": None}  # None = impassable

# Map dimensions
playable_width, playable_height = 40, 40
boundary_width, boundary_height = 50, 50

# Create maps
playable_map = [[random.choice(list(tile_types.keys())) for _ in range(playable_width)] for _ in range(playable_height)]
boundary_map = [[0 for _ in range(boundary_width)] for _ in range(boundary_height)]

# Assuming these dimensions already exist
fog_map = [[False for _ in range(playable_height)] for _ in range(playable_width)]
visibility_map = [[0 for _ in range(playable_height)] for _ in range(playable_width)]

# Centering offsets
offset_x = (boundary_width - playable_width) // 2
offset_y = (boundary_height - playable_height) // 2

# Tile size and zoom
BASE_TILE_WIDTH, BASE_TILE_HEIGHT = 64, 32
TILE_WIDTH, TILE_HEIGHT = BASE_TILE_WIDTH, BASE_TILE_HEIGHT
zoom_level = 1

# Camera (no manual control anymore)
camera_x, camera_y = 0, 0
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

class MessageBox:
    def __init__(self, screen, visible_width, visible_height):
        self.screen = screen
        self.visible_width = visible_width
        self.visible_height = visible_height
        self.message = ""
        self.font = pygame.font.SysFont("Arial", 20)
        self.visible = False
        self.ok_button_rect = None
        self.padding = 20
        self.box_width = 400

    def open(self, message):
        self.message = message
        self.visible = True  # Reset visibility to ensure it is displayed
        self.ok_button_rect = None  # Reset the OK button rect in case it changes

    def close(self):
        self.visible = False

    def draw(self):
        if not self.visible:
            return

        # Word wrapping
        words = self.message.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.font.size(test_line)[0] <= self.box_width - 2 * self.padding:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Calculate height
        line_height = self.font.get_height()
        text_height = line_height * len(lines)
        box_height = text_height + 2 * self.padding + 40  # +40 for button space

        # Center position based on visible screen
        box_x = (self.visible_width - self.box_width) // 2
        box_y = (self.visible_height - box_height) // 2

        # Draw box
        pygame.draw.rect(self.screen, (30, 30, 30), (box_x, box_y, self.box_width, box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, self.box_width, box_height), 2)

        # Draw text
        for i, line in enumerate(lines):
            text_surf = self.font.render(line, True, (255, 255, 255))
            text_x = box_x + (self.box_width - text_surf.get_width()) // 2
            text_y = box_y + self.padding + i * line_height
            self.screen.blit(text_surf, (text_x, text_y))

        # Draw OK button
        button_width = 80
        button_height = 30
        button_x = box_x + (self.box_width - button_width) // 2
        button_y = box_y + box_height - button_height - self.padding // 2
        self.ok_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        pygame.draw.rect(self.screen, (100, 100, 255), self.ok_button_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.ok_button_rect, 2)

        ok_text = self.font.render("OK", True, (255, 255, 255))
        ok_x = button_x + (button_width - ok_text.get_width()) // 2
        ok_y = button_y + (button_height - ok_text.get_height()) // 2
        self.screen.blit(ok_text, (ok_x, ok_y))

class PopupMenu:
    def __init__(self, options,actions, x, y, width=150, item_height=30):
        self.options = options
        self.actions = actions #dictionary to map options to actions
        self.x = x
        self.y = y
        self.width = width
        self.item_height = item_height
        self.selected_index = 0
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 20)

    def open(self, options, actions):
        self.options = options
        self.actions = actions
        self.selected_index = 0
        self.is_open = True

    def close(self):
        self.is_open = False

    def draw(self, screen):
        if not self.is_open:
            return
        height = self.item_height * len(self.options)
        pygame.draw.rect(screen, (0, 0, 0), (self.x, self.y, self.width, height))
        pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.width, height), 2)

        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_index else (255, 255, 255)
            text = self.font.render(option, True, color)
            screen.blit(text, (self.x + 10, self.y + i * self.item_height + 5))

    def set_position(self, x, y):
        self.x = x
        self.y = y  
        
    def move_selection(self, direction):
        if self.is_open:
            self.selected_index = (self.selected_index + direction) % len(self.options)

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


class ResourceSource:
    def __init__(self, x, y, resource_type, amount):
        self.x = x
        self.y = y
        self.resource_type = resource_type  # e.g., "wood", "gold", "food"
        self.amount = amount

    def is_depleted(self):
        return self.amount <= 0

    def gather(self, amount_requested):
        gathered = min(self.amount, amount_requested)
        self.amount -= gathered
        return gathered
    
    def draw(self, screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT):
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
        screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y
        screen_y += TILE_HEIGHT // 2

        for resource in resources:
            if self.resource_type == "food":
                pygame.draw.circle(screen, (128, 0, 128), (int(screen_x), int(screen_y)), 10)
            elif self.resource_type == "gold":
                pygame.draw.circle(screen, (255, 165, 0), (int(screen_x), int(screen_y)), 10)
            else:
                pygame.draw.circle(screen, (0, 100, 0), (int(screen_x), int(screen_y)), 10)

class Villager:
    def __init__(self, x, y, health, movement, mspeed=0.1):
        self.x = x
        self.y = y
        self.health = health
        self.movement_range = movement
        self.speed = mspeed
        self.resources = {"food": 0, "wood": 0, "gold": 0}
        self.selected = False
        self.path = []
        self.previous_position = (x,y)

    def move_along_path(self):
        global popup_message, popup_message_timer
        
        if self.path:
            next_x, next_y = self.path[0]
            
            # Convert to integer for map lookup
            map_x, map_y = int(next_x), int(next_y)
            
            # Verify the tile is still passable
            if (0 <= map_x < playable_width and 
                0 <= map_y < playable_height and 
                tile_types[playable_map[map_x][map_y]] is None):
                popup_message = "Path blocked!"
                popup_message_timer = pygame.time.get_ticks()
                self.path = []
                return
            
        # Rest of movement code...
            dx, dy = next_x - self.x, next_y - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < self.speed:
                self.x, self.y = next_x, next_y
                self.path.pop(0)
            else:
                self.x += self.speed * (dx / dist)
                self.y += self.speed * (dy / dist)

    def draw(self, screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT):
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
        screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y
        screen_y += TILE_HEIGHT // 2

        pygame.draw.circle(screen, (255, 0, 0), (int(screen_x), int(screen_y)), 5)
        if self.selected:
            pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(screen_y)), 8, 2)

class Building:
    def __init__(self, x, y, hitpoints, cost, population_limit=0):
        self.x = x
        self.y = y
        self.hitpoints = hitpoints
        self.cost = cost
        self.population_limit = population_limit
        self.is_constructed = False
        self.selected = False

    def draw(self, screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT):
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
        screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y
        screen_y += TILE_HEIGHT // 2

        pygame.draw.rect(screen, (255, 255, 255), (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT))
        if self.selected:
            pygame.draw.rect(screen, (255, 255, 0), (screen_x - TILE_WIDTH // 2, screen_y - TILE_HEIGHT // 2, TILE_WIDTH, TILE_HEIGHT), 3)

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

# Object initialization
villagers = [
    Villager(5, 5, 100, 5)
]
town_centre = Building(3, 3, 1000, 500, 10)
town_centre.is_constructed = True

resource = [
    ResourceSource(1, 3, "food", 500),
    ResourceSource(3, 1, "gold", 5000),
    ResourceSource(5, 3, "wood", 400)
]

message_box = MessageBox(screen, screen_width, screen_height)
popup_menu = PopupMenu([], {}, 10, 10)

units = villagers
buildings = [town_centre]
resources = resource
population = len(units)

# Tactical map
def draw_tactical_map():
    screen.fill((0, 0, 0))  # Fill screen with black (clear previous frame)
    tile_size = 15
    half_width = tile_size // 2
    half_height = tile_size // 4

    # Calculate center offset for tactical map centering
    map_width_px = (playable_width + playable_height) * half_width
    map_height_px = (playable_width + playable_height) * half_height // 2
    offset_draw_x = (screen_width - map_width_px) // 2
    offset_draw_y = (screen_height - map_height_px) // 2 - screen_height // 2

    # Draw the tactical map tiles (hexagonal or diamond grid)
    for x in range(playable_width):
        for y in range(playable_height):
            vis = visibility_map[x][y]
            tile = playable_map[x][y]

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
        (screen_width, 0),
        (screen_width, screen_height),
        (0, screen_height)
    ]
    iso_points = []
    for sx, sy in corners:
        world_x = (sx - screen_width // 2) - camera_x  # Invert for tactical view
        world_y = (sy - screen_height // 4) - camera_y

        tile_y = ((2 * world_y - world_x) // TILE_HEIGHT) // 2
        tile_x = ((2 * world_y + world_x) // TILE_HEIGHT) // 2

        draw_x = (tile_x - tile_y) * half_width + offset_draw_x + map_width_px // 2
        draw_y = (tile_x + tile_y) * half_height + offset_draw_y + map_height_px // 2
        iso_points.append((draw_x, draw_y))

    pygame.draw.polygon(screen, (255, 255, 0), iso_points, 2)
    pygame.display.flip()

# Pathfinding

def neighbors(x, y):
    for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < playable_width and 0 <= ny < playable_height:
            if tile_types[playable_map[nx][ny]] is not None:
                yield nx, ny

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(start, goal, max_cost):
    heap = [(0, start)]
    came_from = {}
    cost_so_far = {start: 0}
    
    while heap:
        _, current = heapq.heappop(heap)
        if current == goal:
            break
            
        for neighbor in neighbors(*current):
            tile_cost = tile_types[playable_map[neighbor[0]][neighbor[1]]]
            new_cost = cost_so_far[current] + tile_cost
            
            if new_cost > max_cost:  # Respect movement range
                continue
                
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(goal, neighbor)
                heapq.heappush(heap, (priority, neighbor))
                came_from[neighbor] = current
    path = []
    current = goal
    while current != start:
        if current not in came_from:
            return []
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

def bfs_reachable(start, max_cost):
    visited = set()
    queue = deque([(start, 0)])
    reachable = set()
    
    while queue:
        current, cost = queue.popleft()
        
        if current in visited:
            continue
        visited.add(current)
        
        # Only add to reachable if we can stop here
        reachable.add(current)
        
        for neighbor in neighbors(*current):
            tile_cost = tile_types[playable_map[neighbor[0]][neighbor[1]]]
            new_cost = cost + tile_cost
            if new_cost <= max_cost:
                queue.append((neighbor, new_cost))
    
    return reachable

# Tile highlight drawing

def draw_tile_highlight(tx, ty, color, alpha=128):
    draw_tx = tx + offset_x
    draw_ty = ty + offset_y
    screen_x = (draw_tx - draw_ty) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
    screen_y = (draw_tx + draw_ty) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y

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
            (screen_width - popup_menu.width) // 2,
            (screen_height - (popup_menu.item_height * len(popup_menu.options))) // 2
        )

def cancel_action():
    popup_menu.open(actions, callbacks)
    popup_menu.set_position(
        (screen_width - popup_menu.width) // 2,
        (screen_height - (popup_menu.item_height * len(popup_menu.options))) // 2
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

    if not selected_building or not isinstance(selected_building, Building):
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
        new_villager = Villager(spawn_x, spawn_y, 100, 5)
        villagers.append(new_villager)
    else:
        message_box.open("insufficient funds")
        cancel_action()

    popup_menu.close()
    food_amount -= 50

def research_action():
    message_box.open("Researching upgrades")

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
            new_building = Building(selected_tile[0], selected_tile[1], 1000, 500, 10)
            new_building.is_constructed = True
            buildings.append(new_building)
            popup_menu.close()
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
            new_building = Building(selected_tile[0], selected_tile[1], 1000, 500)
            new_building.is_constructed = True
            buildings.append(new_building)
            popup_menu.close()
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

def update_visibility_map(units, buildings, visibility_map, vision_range):
    # Decay all visibility to 1 (seen before but not currently visible)
    for x in range(len(visibility_map)):
        for y in range(len(visibility_map[0])):
            if visibility_map[x][y] == 2:
                visibility_map[x][y] = 1

    # Apply current unit vision (set to 2)
    for unit in units:
        ux, uy = int(unit.x), int(unit.y)
        for dx in range(-vision_range, vision_range + 1):
            for dy in range(-vision_range, vision_range + 1):
                if dx * dx + dy * dy <= vision_range * vision_range:
                    tx = ux + dx
                    ty = uy + dy
                    if 0 <= tx < len(visibility_map) and 0 <= ty < len(visibility_map[0]):
                        visibility_map[tx][ty] = 2


    for building in buildings:
        if getattr(building, 'is_constructed', True):
            bx, by = int(building.x), int(building.y)
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx * dx + dy * dy <= vision_range * vision_range:
                        tx = bx + dx
                        ty = by + dy
                        if 0 <= tx < len(visibility_map) and 0 <= ty < len(visibility_map[0]):
                            visibility_map[tx][ty] = 2


def draw_map_with_fog(map_data, color_func, visibility_map, offset_tx=0, offset_ty=0):
    for tx in range(len(map_data)):
        for ty in range(len(map_data[0])):
            draw_tx = tx + offset_tx
            draw_ty = ty + offset_ty
            screen_x = (draw_tx - draw_ty) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
            screen_y = (draw_tx + draw_ty) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y
            if (-TILE_WIDTH <= screen_x <= screen_width + TILE_WIDTH and
                -TILE_HEIGHT <= screen_y <= screen_height + TILE_HEIGHT):

                # Get base tile color
                color = color_func(tx, ty)

                # Handle visibility
                if visibility_map[tx][ty] == 0:
                    # Fully unseen: draw black
                    color = (0, 0, 0)
                elif visibility_map[tx][ty] == 1:
                    # Previously seen but not currently visible: dim
                    color = tuple(c // 2 for c in color)


                # Draw the tile
                pygame.draw.polygon(screen, color, [
                    (screen_x, screen_y),
                    (screen_x + TILE_WIDTH // 2, screen_y + TILE_HEIGHT // 2),
                    (screen_x, screen_y + TILE_HEIGHT),
                    (screen_x - TILE_WIDTH // 2, screen_y + TILE_HEIGHT // 2)
                ])

def draw_map(map_data, color_func, offset_tx=0, offset_ty=0):
    for tx in range(len(map_data)):
        for ty in range(len(map_data[0])):
            draw_tx = tx + offset_tx
            draw_ty = ty + offset_ty
            screen_x = (draw_tx - draw_ty) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
            screen_y = (draw_tx + draw_ty) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y
            if (-TILE_WIDTH <= screen_x <= screen_width + TILE_WIDTH and
                -TILE_HEIGHT <= screen_y <= screen_height + TILE_HEIGHT):
                color = color_func(tx, ty)
                pygame.draw.polygon(screen, color, [
                    (screen_x, screen_y),
                    (screen_x + TILE_WIDTH // 2, screen_y + TILE_HEIGHT // 2),
                    (screen_x, screen_y + TILE_HEIGHT),
                    (screen_x - TILE_WIDTH // 2, screen_y + TILE_HEIGHT // 2)
                ])

# Draw units, buildings and resources on tactical map
def draw_unit(x, y, half_width, half_height, offset_draw_x, offset_draw_y):
    draw_x = (x - y) * half_width + offset_draw_x + (playable_width * half_width)
    draw_y = (x + y) * half_height + offset_draw_y + (playable_height * half_height) // 2

    triangle_points = [
        (draw_x, draw_y - half_height),
        (draw_x - half_width, draw_y + half_height),
        (draw_x + half_width, draw_y + half_height),
    ]
    pygame.draw.polygon(screen, (255, 255, 255), triangle_points)


def draw_building(x, y, half_width, half_height, offset_draw_x, offset_draw_y):
    draw_x = (x - y) * half_width + offset_draw_x + (playable_width * half_width)
    draw_y = (x + y) * half_height + offset_draw_y + (playable_height * half_height) // 2

    size = half_width // 2
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))


def draw_resource(x, y, half_width, half_height, offset_draw_x, offset_draw_y):
    draw_x = (x - y) * half_width + offset_draw_x + (playable_width * half_width)
    draw_y = (x + y) * half_height + offset_draw_y + (playable_height * half_height) // 2

    radius = half_width // 2
    pygame.draw.circle(screen, (255, 255, 255), (draw_x, draw_y), radius)

# === MAIN LOOP === #

while running:
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
                if event.key == pygame.K_s and selected_tile[1] < playable_height - 1:
                    selected_tile = (selected_tile[0], selected_tile[1] + 1)
                if event.key == pygame.K_a and selected_tile[0] > 0:
                    selected_tile = (selected_tile[0] - 1, selected_tile[1])
                if event.key == pygame.K_d and selected_tile[0] < playable_width - 1:
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
                    reachable_tiles = bfs_reachable((int(selected_unit.x), int(selected_unit.y)), selected_unit.movement_range)

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
                            selected_unit.selected = True
                            selected_tile = (int(selected_unit.x), int(selected_unit.y))
                            reachable_tiles = bfs_reachable((int(unit.x), int(unit.y)), unit.movement_range)
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
                                    (screen_width - popup_menu.width) // 2,
                                    (screen_height - (popup_menu.item_height * len(popup_menu.options))) // 2
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

                if event.key == pygame.K_SPACE and selected_unit:
                    tactical_map_mode = False
                    if selected_tile in reachable_tiles:
                        selected_unit.previous_position = (selected_unit.x, selected_unit.y)
                        start_pos = (int(selected_unit.x), int(selected_unit.y))

                        if selected_tile == start_pos:
                            selected_unit.path = [(float(selected_unit.x), float(selected_unit.y))]
                            is_moving = True
                        else:
                            path = a_star(start_pos, selected_tile, selected_unit.movement_range)
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

    if is_moving and not selected_unit.path:
        is_moving = False
        if tactical_map_queued and last_tactical_key == "m":
            tactical_map_mode = not tactical_map_mode
        tactical_map_queued = False
        last_tactical_key = None

    hovered_tile = selected_tile

    # Convert hovered tile to screen coordinates
    draw_x = hovered_tile[0] + offset_x
    draw_y = hovered_tile[1] + offset_y
    screen_x = (draw_x - draw_y) * TILE_WIDTH // 2 + (screen_width // 2) + camera_x
    screen_y = (draw_x + draw_y) * TILE_HEIGHT // 2 + (screen_height // 4) + camera_y

    # Scroll if tile is near screen edges
    margin = 50  # pixels from screen edge to trigger camera move
    scroll_speed = 10

    if screen_x < margin:
        camera_x += scroll_speed
    elif screen_x > screen_width - margin:
        camera_x -= scroll_speed

    if screen_y < margin:
        camera_y += scroll_speed
    elif screen_y > screen_height - margin:
        camera_y -= scroll_speed

    if is_moving:
        selected_unit.move_along_path()
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
                (screen_width - popup_menu.width) // 2,
                (screen_height - (popup_menu.item_height * len(popup_menu.options))) // 2
            )


    if tactical_map_mode:
        draw_tactical_map()
        clock.tick(30)
        continue

    update_visibility_map(units, buildings, visibility_map, vision_range=3)

    screen.fill((0, 0, 0))

    # Draw boundary normally
    draw_map(boundary_map, lambda tx, ty: (40, 40, 40) if (tx + ty) % 2 == 0 else (30, 30, 30))

    draw_map_with_fog(
        playable_map,
        lambda tx, ty: (
            (34, 177, 76) if playable_map[tx][ty] == "G" else
            (0, 162, 232) if playable_map[tx][ty] == "W" else
            (127, 127, 127)
        ),
        visibility_map,
        offset_x,
        offset_y
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
        building.draw(screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT)
    for resource in resources:
        resource.draw(screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT)
    for unit in units:
        unit.draw(screen, offset_x, offset_y, camera_x, camera_y, TILE_WIDTH, TILE_HEIGHT)

    # === RESOURCE AND POPULATION DISPLAY BAR === #
    bar_height = 40
    bar_color = (20, 20, 20)
    text_color = (255, 255, 255)
    font = pygame.font.SysFont(None, 24)

    # Fill top bar background
    pygame.draw.rect(screen, bar_color, (0, 0, screen_width, bar_height))

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

    # Center vertically, offset slightly from left
    screen.blit(text_surface, (10, (bar_height - text_surface.get_height()) // 2))

    popup_menu.draw(screen)
    message_box.draw()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
