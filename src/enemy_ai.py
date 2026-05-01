import random
from buildings.base_buildings import BaseBuildings
from path_finding import PathFinding
from target_aquisition import TargetAquisition
from units.base_units import BaseUnits
from config import *

class EnemyAi():
    def __init__(self, path_enemies):
        self.target_aquisition = TargetAquisition()
        self.path_enemies = path_enemies
        self.enemy_construction_tasks = {}

    def execute_turn(self, enemy_units, player_units, player_buildings, resource_list, enemy_buildings, gameplay_state):
        # Handle Villagers and get targets for military
        contested_tiles = self.manage_villagers(enemy_units, player_units, resource_list, enemy_buildings, player_buildings, gameplay_state)
        
        # Handle Economy/Construction
        self.manage_economy(enemy_units, enemy_buildings, resource_list, gameplay_state)
        
        # Handle Military
        self.manage_military(enemy_units, player_units, player_buildings, enemy_buildings, contested_tiles)

    # Finding resources and identifying contested tiles.
    def manage_villagers(self, enemy_units, player_units, resource_list, enemy_buildings, player_buildings, gameplay_state):
        """Logic for finding resources with a priority on low stockpiles."""
        contested_tiles = []
        claimed_resource_ids = []
        
        pf = PathFinding(player_units, enemy_units, player_buildings, enemy_buildings, moving_side='enemy')
        villagers = [u for u in enemy_units if getattr(u, "type", "") == "villager" and u.health > 0]
        
        # Identify villagers already on resources (Don't move them)
        for v in villagers:
            if getattr(v, "is_gathering", False):
                claimed_resource_ids.append(getattr(v, "gather_resource_id", -1))
                continue
                
            for res in resource_list:
                if not res.is_depleted() and int(v.x) == int(res.x) and int(v.y) == int(res.y):
                    v.is_gathering = True
                    v.gather_resource_id = res.id
                    v.path = [] 
                    claimed_resource_ids.append(res.id)
                    break

        # Determine which resource type the AI needs most
        stockpiles = {
            'gold': getattr(gameplay_state, 'enemy_gold', 0),
            'wood': getattr(gameplay_state, 'enemy_wood', 0),
            'food': getattr(gameplay_state, 'enemy_food', 0)
        }
        # Sort types by lowest amount first
        priority_order = sorted(stockpiles, key=stockpiles.get)

        # Assign new resources to idle villagers
        for v in villagers:
            if getattr(v, "is_gathering", False): 
                continue

            best_res = None
            
            # Try to find a resource based on priority order
            for target_type in priority_order:
                min_dist = float('inf')
                
                for res in resource_list:
                    # Check if it matches the current priority type (e.g., 'gold')
                    if getattr(res, 'type', '').lower() != target_type:
                        continue
                    if res.is_depleted() or res.id in claimed_resource_ids:
                        continue
                    
                    # Check if occupied by anyone
                    unit_on_tile = self.get_unit_at(res.x, res.y, enemy_units + player_units)
                    if unit_on_tile:
                        # If it's a player, mark it for military but don't path villager there yet
                        if unit_on_tile in player_units:
                            contested_tiles.append((int(res.x), int(res.y)))
                        continue 

                    dist = abs(v.x - res.x) + abs(v.y - res.y)
                    if dist < min_dist:
                        min_dist = dist
                        best_res = res
                
                # If we found the priority resource, stop looking for other types
                if best_res:
                    break

            # If no priority resource found, default to the closest resource of ANY type
            if not best_res:
                min_dist = float('inf')
                for res in resource_list:
                    if not res.is_depleted() and res.id not in claimed_resource_ids:
                        dist = abs(v.x - res.x) + abs(v.y - res.y)
                        if dist < min_dist:
                            min_dist = dist
                            best_res = res

            # Pathfinding to the chosen resource
            if best_res:
                claimed_resource_ids.append(best_res.id)
                path = pf.a_star((int(v.x), int(v.y)), (int(best_res.x), int(best_res.y)), 100)
                if path:
                    steps = min(v.movement_range, len(path))
                    v.path = [(float(x), float(y)) for x, y in path[:steps]]

        return contested_tiles

    def manage_economy(self, enemy_units, enemy_buildings, resource_list, gameplay_state):
        villagers = [u for u in enemy_units if getattr(u, "type", "") == "villager" and u.health > 0]
        if not villagers: return

        building_goals = {
            "town_center": 1,
            "market": 1,
            "house": (gameplay_state.enemy_max_population // 5) + 1,
            "barracks": 1
        }

        current_counts = {}
        for b in enemy_buildings:
            current_counts[b.type] = current_counts.get(b.type, 0) + 1

        for b_type, goal in building_goals.items():
            if current_counts.get(b_type, 0) < goal:
                if self.can_afford_building(b_type, gameplay_state):
                    
                    potential_builders = [v for v in villagers if not v.is_gathering and v not in self.enemy_construction_tasks]
                    
                    for builder in potential_builders:
                        tx, ty = int(builder.x), int(builder.y)
                        
                        # Check Player Buildings
                        is_blocked = any(int(b.x) == tx and int(b.y) == ty for b in gameplay_state.buildings)
                        # Check Enemy Buildings (This catches the Town Centre)
                        is_blocked |= any(int(b.x) == tx and int(b.y) == ty for b in gameplay_state.e_buildings)
                        # Check Resources
                        is_blocked |= any(int(r.x) == tx and int(r.y) == ty for r in gameplay_state.resources)

                        if not is_blocked:
                            self.request_construction(b_type, builder, gameplay_state)
                            return 
                        else:
                            self.move_to_clear_ground(builder, gameplay_state)

    def manage_military(self, enemy_units, player_units, player_buildings, enemy_buildings, contested_tiles):
        """Logic for military movement and attacking contested resource tiles."""
        military = [u for u in enemy_units if getattr(u, "type", "") != "villager" and u.health > 0]
        pf = PathFinding(player_units, enemy_units, player_buildings, enemy_buildings, moving_side='enemy')

        for m in military:
            target_pos = None
            
            # Priority 1: Clear contested resource tiles
            if contested_tiles:
                # Find closest contested tile to this specific unit
                contested_tiles.sort(key=lambda pos: abs(m.x - pos[0]) + abs(m.y - pos[1]))
                target_pos = contested_tiles.pop(0) 

            # Priority 2: Standard attack (Player units/buildings)
            if not target_pos:
                nearest_target = self.find_nearest_target(m, player_units, player_buildings)
                if nearest_target:
                    target_pos = (int(nearest_target.x), int(nearest_target.y))

            if target_pos:
                path = pf.a_star((int(m.x), int(m.y)), target_pos, 100)
                if path:
                    if path[-1] == target_pos: path.pop() # Stop adjacent to attack
                    steps = min(m.movement_range, len(path))
                    m.path = [(float(x), float(y)) for x, y in path[:steps]]
    
    def manage_research(self, enemy_buildings, gameplay_state):
        """Automated research logic for the Enemy AI."""
        for building in enemy_buildings:
            if not building.is_constructed or building.action_count <= 0:
                continue
            
            if building.type in BUILDINGS:
                tech_list = BUILDINGS[building.type][8]
            elif building.type in RESOURCE_BUILDINGS:
                tech_list = RESOURCE_BUILDINGS[building.type][9]
            else:
                continue

            affordable_techs = []
            for r_key in tech_list:
                r_attr = RESEARCH[r_key]
                
                # Check resources
                can_afford = (
                    gameplay_state.enemy_food >= r_attr[1] and 
                    gameplay_state.enemy_wood >= r_attr[2] and 
                    gameplay_state.enemy_gold >= r_attr[3]
                )

                if can_afford:
                    # Ensure they haven't already researched it or have it in queue
                    if r_key not in gameplay_state.enemy_researched_techs and \
                    r_key not in gameplay_state.enemy_pending_techs:
                        affordable_techs.append(r_key)

            if affordable_techs:
                chosen_tech = random.choice(affordable_techs)
                
                self.execute_enemy_research(chosen_tech, building, gameplay_state)
                
                # One research project per building per turn

    # --- Helper Methods ---

    def can_afford_building(self, b_type, gameplay_state):
        # Assuming BUILDINGS[b_type] = [name, food, wood, gold, ...]
        costs = BUILDINGS.get(b_type)
        if not costs: return False
        return (gameplay_state.enemy_food >= costs[1] and 
                gameplay_state.enemy_wood >= costs[2] and 
                gameplay_state.enemy_gold >= costs[3])

    def can_afford_tech(self, tech_name, gameplay_state):
        # Assuming a TECHS dictionary exists in your config
        costs = RESEARCH.get(tech_name)
        if not costs: return False
        return (gameplay_state.enemy_food >= costs['food'] and 
                gameplay_state.enemy_wood >= costs['wood'] and 
                gameplay_state.enemy_gold >= costs['gold'])
    
    def execute_enemy_research(self, tech_key, building, gameplay_state):
        """Deducts costs and adds to the enemy's pending queue."""
        r_attr = RESEARCH[tech_key]
        
        # Deduct Enemy Resources
        gameplay_state.enemy_food -= r_attr[1]
        gameplay_state.enemy_wood -= r_attr[2]
        gameplay_state.enemy_gold -= r_attr[3]

        # Add to the enemy-specific pending list
        gameplay_state.enemy_pending_techs.append(tech_key)
        
        # Mark building as used
        building.rest()
        print(f"Enemy AI started researching: {r_attr[0]}")
    
    def get_unit_at(self, x, y, unit_list):
        return next((u for u in unit_list if int(u.x) == int(x) and int(u.y) == int(y) and u.health > 0), None)

    def find_nearest_target(self, unit, player_units, player_buildings):
        targets = [p for p in player_units if p.health > 0] + [b for b in player_buildings if b.hitpoints > 0]
        if not targets: return None
        return min(targets, key=lambda t: abs(unit.x - t.x) + abs(unit.y - t.y))
    
    def is_tile_occupied(self, tx, ty, gameplay_state):
        # Boundaries
        if not (0 <= tx < BOUNDARY_WIDTH and 0 <= ty < BOUNDARY_HEIGHT):
            return True

        # Units (Player + Enemy)
        if any(int(u.x) == tx and int(u.y) == ty for u in gameplay_state.units): return True
        if any(int(u.x) == tx and int(u.y) == ty for u in gameplay_state.enemy_units): return True

        # Buildings (Player + Enemy)
        if any(int(b.x) == tx and int(b.y) == ty for b in gameplay_state.buildings): return True
        if any(int(b.x) == tx and int(b.y) == ty for b in gameplay_state.e_buildings): return True

        # Resources
        if any(int(r.x) == tx and int(r.y) == ty for r in gameplay_state.resources): return True

        return False
    
    def move_to_clear_ground(self, villager, gameplay_state):
        """Moves a villager to an adjacent empty tile if they are standing on a building."""
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,-1)]:
            nx, ny = int(villager.x) + dx, int(villager.y) + dy
            
            # Use your existing is_tile_occupied check
            if not self.is_tile_occupied(nx, ny, gameplay_state):
                villager.path = [(float(nx), float(ny))]
                break

    def request_construction(self, building_type, villager, gameplay_state):
        # Use villager's exact current position
        tx, ty = int(villager.x), int(villager.y)
        b_attr = BUILDINGS[building_type]
        
        # Visual cleanup
        gameplay_state.cover_resources(tx, ty)
        
        # Create foundation
        new_building_id = max([b.id for b in gameplay_state.e_buildings], default=0) + 1
        new_building = BaseBuildings(tx, ty, b_attr[4], b_attr[5])
        new_building.id = new_building_id
        new_building.type = building_type
        new_building.is_constructed = False

        gameplay_state.e_buildings.append(new_building)
        
        # Task the villager
        villager.rest()
        # Ensure they stop moving and stay on this tile to work
        villager.path = [] 
        self.enemy_construction_tasks[villager] = new_building 

        # Pay for the building
        gameplay_state.enemy_food -= b_attr[1]
        gameplay_state.enemy_wood -= b_attr[2]
        gameplay_state.enemy_gold -= b_attr[3]

    def plan_military_infrastructure(self, gameplay_state):
        """Placeholder for future military building logic."""
        pass

    def train_enemy_units(self, e_buildings, enemy_units, gameplay_state):
        """Processes unit production at enemy buildings with villager limits."""
        
        # Calculate current villager count once at the start of training
        current_villagers = [u for u in enemy_units if getattr(u, "type", "") == "villager"]
        villager_count = len(current_villagers)
        VILLAGER_LIMIT = 5

        for building in e_buildings:
            if not building.is_constructed:
                continue
            if building.type not in BUILDINGS:
                continue

            # Check if spawn location is blocked
            spawn_x, spawn_y = building.x, building.y
            spawn_blocked = any(
                int(u.x) == spawn_x and int(u.y) == spawn_y for u in enemy_units
            )
            if spawn_blocked:
                continue

            # Acquire building attribute list (index 6 is trainable units)
            b_attr = BUILDINGS[building.type]
            trainable_units = b_attr[6]

            #  Collect all affordable units, applying specific rules
            affordable_units = []
            for unit_name in trainable_units:
                # RULE: Only Town Centers can create villagers
                if unit_name == "villager" and "town" not in building.type.lower():
                    continue

                # RULE: Cap villagers at 5
                if unit_name == "villager" and villager_count >= VILLAGER_LIMIT:
                    continue

                # Standard resource check
                u_attr = UNITS[unit_name]
                food, wood, gold = u_attr[1], u_attr[2], u_attr[3]
                
                if (gameplay_state.enemy_food >= food and
                    gameplay_state.enemy_wood >= wood and
                    gameplay_state.enemy_gold >= gold):
                    affordable_units.append(unit_name)

            # Randomly spawn from the filtered list
            if affordable_units:
                unit_name = random.choice(affordable_units)
                u_attr = UNITS[unit_name]
                food, wood, gold = u_attr[1], u_attr[2], u_attr[3]
                
                new_unit = BaseUnits(
                    spawn_x, spawn_y,
                    u_attr[5], u_attr[6], u_attr[7], u_attr[8], type=unit_name
                )
                
                print(f"Enemy spawns: {unit_name} at ({spawn_x}, {spawn_y})")
                enemy_units.append(new_unit)
                
                # Deduct resources
                gameplay_state.enemy_food -= food
                gameplay_state.enemy_wood -= wood
                gameplay_state.enemy_gold -= gold
                
                # Update villager count immediately if a villager was just born
                if unit_name == "villager":
                    villager_count += 1
                
                building.rest()
                # Only one unit per building per turn