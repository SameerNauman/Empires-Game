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

    def execute_turn(self, enemy_units, player_units, player_buildings, resource_list, enemy_buildings, gameplay_state):
        for b in enemy_buildings:
            if b.is_constructed:
                b.rested()

        # Handle Villagers and get targets for military
        contested_tiles = self.manage_villagers(enemy_units, player_units, resource_list, enemy_buildings, player_buildings, gameplay_state)
        
        # Handle Economy/Construction
        self.manage_economy(enemy_units, enemy_buildings, resource_list, gameplay_state)

        # Handle Research
        self.manage_research(enemy_buildings, gameplay_state)
        
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
                    
                    potential_builders = [v for v in villagers if not v.is_gathering and v not in gameplay_state.construction]
                    
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
                            break 
                        else:
                            self.move_to_clear_ground(builder, gameplay_state)
                            break

        current_age_data = AGES.get(gameplay_state.enemy_age)
        if current_age_data and "next_age" in current_age_data:
            # AI checks if it meets the tech requirement and has surplus resources
            if len(gameplay_state.enemy_researched_techs) >= current_age_data["req_techs"]:
                # AI will attempt to age up if it has 20% more than the required cost (buffer)
                if gameplay_state.enemy_food >= current_age_data["food"] * 1.2:
                    gameplay_state.attempt_age_up('enemy')

    def manage_military(self, enemy_units, player_units, player_buildings, enemy_buildings, contested_tiles):
        """Logic for military movement and attacking based on valid adjacent tiles."""
        military = [u for u in enemy_units if getattr(u, "type", "") != "villager" and u.health > 0]
        if not military:
            return

        pf = PathFinding(player_units, enemy_units, player_buildings, enemy_buildings, moving_side='enemy')

        for m in military:
            # Skip if the unit is already on its way somewhere
            if getattr(m, "path", []):
                continue

            target_obj = None
            target_pos = None
            
            # Priority 1: Clear contested resource tiles
            if contested_tiles:
                closest_tile = min(contested_tiles, key=lambda pos: abs(m.x - pos[0]) + abs(m.y - pos[1]))
                target_pos = closest_tile

            # Priority 2: Standard attack (Player units/buildings)
            if not target_pos:
                target_obj = self.find_nearest_target(m, player_units, player_buildings)
                if target_obj:
                    target_pos = (int(target_obj.x), int(target_obj.y))

            # Execute Turn-Based Pathfinding & Combat Positioning
            if target_pos:
                start_pos = (int(m.x), int(m.y))
                
                # --- CASE 1: ATTACKING AN OCCUPIED PLAYER TILE/STRUCTURE ---
                # If we are pursuing an active player element, we must path to an ADJACENT tile
                if target_obj:
                    attack_range = getattr(m, "attack_range", 1)
                    if getattr(target_obj, "type", "") == "building":
                        attack_range = 1  # Force structural attacks to be melee adjacent

                    # Is the target already sitting comfortably within our range?
                    current_dist = abs(start_pos[0] - target_pos[0]) + abs(start_pos[1] - target_pos[1])
                    if current_dist <= attack_range:
                        # Target is in range, clear path to remain stationary and strike
                        m.path = []
                        continue

                    # Generate valid fallback tiles surrounding the target based on attack range
                    valid_combat_tiles = []
                    
                    # Look at offsets around the target tile matching our combat range capabilities
                    for dx in range(-attack_range, attack_range + 1):
                        for dy in range(-attack_range, attack_range + 1):
                            if abs(dx) + abs(dy) == attack_range: # Check exact range distance
                                tx, ty = target_pos[0] + dx, target_pos[1] + dy
                                
                                # Make sure the standpoint tile is within the map bounds
                                if 0 <= tx < len(PLAYABLE_MAP) and 0 <= ty < len(PLAYABLE_MAP[tx]):
                                    # Ensure the fallback tile isn't blocked by other player elements
                                    if not pf.is_friendly(tx, ty) and not pf.is_player_building(tx, ty):
                                        valid_combat_tiles.append((tx, ty))

                    # Find the closest legal tile to our military unit to target
                    if valid_combat_tiles:
                        best_standpoint = min(valid_combat_tiles, key=lambda pos: abs(start_pos[0] - pos[0]) + abs(start_pos[1] - pos[1]))
                        
                        # Calculate path to the standpoint tile (which is empty and legal for A*)
                        path = pf.a_star(start_pos, best_standpoint, 100)
                        
                        if path:
                            if path[0] == start_pos:
                                path.pop(0)
                            steps = min(m.movement_range, len(path))
                            m.path = [(float(x), float(y)) for x, y in path[:steps]]
                            
                # --- CASE 2: MOVING TO AN UNBROKEN CONTESTED GROUND TILE ---
                else:
                    # Contested resource tiles are empty, meaning A* can target them directly
                    path = pf.a_star(start_pos, target_pos, 100)
                    if path:
                        if path[0] == start_pos:
                            path.pop(0)
                        steps = min(m.movement_range, len(path))
                        m.path = [(float(x), float(y)) for x, y in path[:steps]]
    
    def manage_research(self, enemy_buildings, gameplay_state):
        # Shuffle to give the Market a fair chance at resources
        shuffled_buildings = list(enemy_buildings)
        random.shuffle(shuffled_buildings)
        
        for building in shuffled_buildings:
            # Debug: Is the AI even looking at the market?
            if not building.is_constructed or building.action_count == 2:
                continue
            
            # Safely get tech list
            if building.type in BUILDINGS:
                tech_list = BUILDINGS[building.type][8]
            elif building.type in RESOURCE_BUILDINGS:
                tech_list = RESOURCE_BUILDINGS[building.type][9]

            # Check affordability
            for tech_key in tech_list:
                if tech_key in gameplay_state.enemy_researched_techs or tech_key in gameplay_state.enemy_pending_techs:
                    continue
                
                t_attr = RESEARCH.get(tech_key)
                if not t_attr: continue
                
                if (gameplay_state.enemy_food >= t_attr[1] and 
                    gameplay_state.enemy_wood >= t_attr[2] and 
                    gameplay_state.enemy_gold >= t_attr[3]):
                    
                    self.execute_enemy_research(tech_key, building, gameplay_state)
                    break # Building used its action, move to next building

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
        
        gameplay_state.enemy_food -= r_attr[1]
        gameplay_state.enemy_wood -= r_attr[2]
        gameplay_state.enemy_gold -= r_attr[3]

        # Ensure your GameplayState logic handles 'enemy_pending_techs' 
        # separately from 'player_pending_techs'!
        gameplay_state.enemy_pending_techs.append(tech_key)
        
        building.rest()
        print(f"Enemy AI started researching: {r_attr[0]} at {building.type}")
    
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
        new_building.building_queued()
        new_building.is_constructed = False

        gameplay_state.e_buildings.append(new_building)
        
        # Task the villager
        villager.rest()
        # Ensure they stop moving and stay on this tile to work
        villager.path = [] 
        gameplay_state.construction[villager] = new_building 

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