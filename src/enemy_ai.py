import random, math
from buildings.base_buildings import BaseBuildings
from path_finding import PathFinding
from target_aquisition import TargetAquisition
from units.base_units import BaseUnits
from config import *

class EnemyAi():
    def __init__(self, path_enemies=None):
        # Initialize the AI with a target acquisition system and a list of pathfinding enemies
        self.target_aquisition = TargetAquisition()
        self.path_enemies = path_enemies
        self.military_goals = {"Dark Age": {"barracks": 1, "units": 3}}

    # Execute the AI's turn, managing villagers, economy, research, and military actions
    def execute_turn(self, enemy_units, player_units, player_buildings, resource_list, enemy_buildings, gameplay_state):
        # Rest all constructed buildings to reset their action count for the turn
        for b in enemy_buildings:
            if b.is_constructed:
                b.rested()

        if gameplay_state.attempt_age_up("enemy") is True:
            return

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
        # Identify villagers and assign them to gather resources based on priority and availability.
        contested_tiles = []
        claimed_resource_ids = []

        # Pathfinding instance for villagers to find resources
        pf = PathFinding(player_units, enemy_units, player_buildings, enemy_buildings, moving_side='enemy')
        # Identify all active villagers that are not dead
        villagers = [u for u in enemy_units if getattr(u, "type", "") == "villager" and u.health > 0]
        
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
                    if getattr(res, 'resource_type', getattr(res, 'type', '')).lower() != target_type:
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
                    if (not res.is_depleted() and res.id not in claimed_resource_ids
                            and not self.get_unit_at(res.x, res.y, enemy_units + player_units)
                            and self.is_passable_tile(int(res.x), int(res.y))):
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

        target_mills = max(2, 1 + (len(villagers) // 3))
        target_farms = target_mills * 2
        target_gold_mines = 3 if gameplay_state.enemy_gold < 500 else 2

        military_goals = self.military_goals.get(gameplay_state.enemy_age, {})
        building_goals = {"town_centre": 1}
        if military_goals:
            building_goals["barracks"] = military_goals["barracks"]
        building_goals.update({
            "mill": target_mills,
            "farm": target_farms,
            "gold_mine": target_gold_mines
        })

        # Count current buildings of each type
        current_counts = {}
        for b in enemy_buildings:
            current_counts[b.type] = current_counts.get(b.type, 0) + 1

        assigned_builders = set()
        reserved_build_tiles = set()
        pf = PathFinding(
            gameplay_state.units, enemy_units, gameplay_state.buildings,
            enemy_buildings, moving_side='enemy'
        )

        for b_type, goal in building_goals.items():
            while current_counts.get(b_type, 0) < goal:
                print(f"Checking {b_type}: Current={current_counts.get(b_type, 0)}, Goal={goal}")
                if not self.can_afford_building(b_type, gameplay_state):
                    print(f"-> Cannot afford {b_type} yet.")
                    break

                potential_builders = [
                    v for v in villagers
                    if v not in gameplay_state.construction and v not in assigned_builders
                ]
                print(f"-> Available builders: {len(potential_builders)}")
                assigned_goal = False

                for builder in potential_builders:
                    build_sites = self.get_build_sites(
                        b_type, builder, gameplay_state, reserved_build_tiles
                    )
                    for build_tile in build_sites:
                        tx, ty = int(builder.x), int(builder.y)
                        if self.unit_is_on_tile(builder, build_tile):
                            if self.request_construction(b_type, builder, gameplay_state, build_tile):
                                print(f"Enemy AI building {b_type} at ({build_tile[0]}, {build_tile[1]})")
                                assigned_goal = True
                        else:
                            path = pf.a_star((tx, ty), build_tile, 100)
                            if path:
                                steps = min(builder.movement_range, len(path))
                                builder.path = [(float(x), float(y)) for x, y in path[:steps]]
                                assigned_goal = True

                        if assigned_goal:
                            assigned_builders.add(builder)
                            reserved_build_tiles.add(build_tile)
                            current_counts[b_type] = current_counts.get(b_type, 0) + 1
                            break
                    if assigned_goal:
                        break

                if not assigned_goal:
                    break

    # Manage military units by determining their targets, calculating paths, and executing attacks or movements based on the game state.
    def manage_military(self, enemy_units, player_units, player_buildings, enemy_buildings, contested_tiles):
        # Identify all active military units that are not dead
        military = [u for u in enemy_units if getattr(u, "type", "") != "villager" and u.health > 0]
        if not military:
            return

        # Pathfinding instance for military units to find targets
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

            if target_pos:
                start_pos = (int(m.x), int(m.y))
                
                if target_obj:
                    # Attack range is determined by the unit's attributes, defaulting to 1 if not specified
                    attack_range = getattr(m, "attack_range", 1)
                    # If the target is a building, force the attack range to be melee adjacent
                    if getattr(target_obj, "type", "") == "building":
                        attack_range = 1  # Force structural attacks to be melee adjacent

                    # Check if the target is within attack range
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
                            
                # If no target object was found, but we have a contested tile, we can still path to it
                else:
                    # Contested resource tiles are empty, meaning A* can target them directly
                    path = pf.a_star(start_pos, target_pos, 100)
                    if path:
                        if path[0] == start_pos:
                            path.pop(0)
                        steps = min(m.movement_range, len(path))
                        m.path = [(float(x), float(y)) for x, y in path[:steps]]
    
    # Manage research by checking if the AI can afford technologies, and if so, queue them for research at appropriate buildings.
    def manage_research(self, enemy_buildings, gameplay_state):
        required_techs = AGES.get(gameplay_state.enemy_age, {}).get("req_techs")
        if required_techs is not None and (
            len(gameplay_state.enemy_researched_techs) + len(gameplay_state.enemy_pending_techs)
            >= required_techs
        ):
            return

        # Shuffle buildings to randomize research order
        shuffled_buildings = list(enemy_buildings)
        random.shuffle(shuffled_buildings)
        
        for building in shuffled_buildings:
            if required_techs is not None and (
                len(gameplay_state.enemy_researched_techs) + len(gameplay_state.enemy_pending_techs)
                >= required_techs
            ):
                break

            # Debug: Is the AI even looking at the market?
            if not building.is_constructed or building.action_count == 2:
                continue
            
            building_data = gameplay_state.get_building_data(
                building.type, gameplay_state.enemy_faction
            )
            tech_list = building_data.get("research", []) if building_data else []

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

    def can_afford_building(self, b_type, gameplay_state):
        building_data = gameplay_state.get_building_data(
            b_type, gameplay_state.enemy_faction
        )
        if not building_data:
            return False

        costs = building_data["cost"]
        return (gameplay_state.enemy_food >= costs["food"] and
                gameplay_state.enemy_wood >= costs["wood"] and
                gameplay_state.enemy_gold >= costs["gold"])

    def can_afford_tech(self, tech_name, gameplay_state):
        # Assuming a TECHS dictionary exists in your config
        costs = RESEARCH.get(tech_name)
        if not costs: return False
        return (gameplay_state.enemy_food >= costs['food'] and 
                gameplay_state.enemy_wood >= costs['wood'] and 
                gameplay_state.enemy_gold >= costs['gold'])

    # Execute the research process for a given technology, deducting resources and queuing it for completion.
    def execute_enemy_research(self, tech_key, building, gameplay_state):
        r_attr = RESEARCH[tech_key]
        
        gameplay_state.enemy_food -= r_attr[1]
        gameplay_state.enemy_wood -= r_attr[2]
        gameplay_state.enemy_gold -= r_attr[3]

        gameplay_state.enemy_pending_techs.append(tech_key)
        
        building.rest()
        print(f"Enemy AI started researching: {r_attr[0]} at {building.type}")
    
    def get_unit_at(self, x, y, unit_list):
        return next((u for u in unit_list if int(u.x) == int(x) and int(u.y) == int(y) and u.health > 0), None)

    # Find the nearest target (player unit or building) for a given enemy unit, prioritizing proximity.
    def find_nearest_target(self, unit, player_units, player_buildings):
        targets = [p for p in player_units if p.health > 0] + [b for b in player_buildings if b.hitpoints > 0]
        if not targets: return None
        return min(targets, key=lambda t: abs(unit.x - t.x) + abs(unit.y - t.y))
    
    def is_tile_occupied(self, tx, ty, gameplay_state):
        # Boundaries
        if not (0 <= tx < PLAYABLE_WIDTH and 0 <= ty < PLAYABLE_HEIGHT):
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

    # Move a villager to an adjacent unoccupied tile if their current tile is blocked, ensuring they can perform 
    # construction or gathering tasks.
    def move_to_clear_ground(self, villager, gameplay_state):
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = int(villager.x) + dx, int(villager.y) + dy
            
            if self.is_passable_tile(nx, ny) and not self.is_tile_occupied(nx, ny, gameplay_state):
                villager.path = [(float(nx), float(ny))]
                break

    def request_construction(self, building_type, villager, gameplay_state, build_tile=None):
        tx, ty = map(int, build_tile or (villager.x, villager.y))

        if not self.is_passable_tile(tx, ty) or not self.unit_is_on_tile(villager, (tx, ty)):
            return False
        if any(int(b.x) == tx and int(b.y) == ty for b in gameplay_state.buildings + gameplay_state.e_buildings):
            return False
        if any(
            unit is not villager and int(unit.x) == tx and int(unit.y) == ty
            for unit in gameplay_state.units + gameplay_state.enemy_units
        ):
            return False

        building_data = gameplay_state.get_building_data(
            building_type, gameplay_state.enemy_faction
        )
        if not building_data:
            return False

        costs = building_data["cost"]
        if (gameplay_state.enemy_food < costs["food"]
                or gameplay_state.enemy_wood < costs["wood"]
                or gameplay_state.enemy_gold < costs["gold"]):
            return False

        stats = building_data["stats"]
        
        gameplay_state.cover_resources(tx, ty)
        
        # Create foundation
        new_building_id = max([b.id for b in gameplay_state.e_buildings], default=0) + 1
        new_building = BaseBuildings(
            tx, ty,
            stats["hitpoints"] + gameplay_state.enemy_tech_multipliers.get("building_hitpoints", 0),
            stats.get("pop capacity", 0),
            type=building_type, loyalty="enemy"
        )
        new_building.id = new_building_id
        
        # Ensure ALL buildings start queued as foundations
        new_building.building_queued()
        new_building.is_constructed = False

        gameplay_state.e_buildings.append(new_building)
        
        # If it's a resource building, spawn resource source
        resource_data = building_data.get("resource")
        if resource_data:
            new_resource = ResourceSource(
                tx, ty, resource_data["type"], resource_data["amount"],
                resource_data["gather_amount"], building_data["description"], True, "enemy"
            )
            gameplay_state.resources.append(new_resource)
        
        # Task the villager
        villager.rest()
        villager.path = [] 
        gameplay_state.construction[villager] = new_building 

        # Pay for building
        gameplay_state.enemy_food -= costs["food"]
        gameplay_state.enemy_wood -= costs["wood"]
        gameplay_state.enemy_gold -= costs["gold"]
        return True

    def is_passable_tile(self, tx, ty):
        if not (0 <= tx < len(PLAYABLE_MAP) and 0 <= ty < len(PLAYABLE_MAP[tx])):
            return False
        tile_type = PLAYABLE_MAP[tx][ty]
        return tile_type in TILE_TYPES and TILE_TYPES[tile_type] is not None

    def unit_is_on_tile(self, unit, tile):
        return (
            math.isclose(float(unit.x), tile[0], abs_tol=1e-6)
            and math.isclose(float(unit.y), tile[1], abs_tol=1e-6)
        )

    def is_build_site_available(self, tx, ty, builder, gameplay_state, reserved_build_tiles, allow_resources=False):
        if not self.is_passable_tile(tx, ty) or (tx, ty) in reserved_build_tiles:
            return False
        if any(int(b.x) == tx and int(b.y) == ty for b in gameplay_state.buildings + gameplay_state.e_buildings):
            return False
        if any(
            unit is not builder and int(unit.x) == tx and int(unit.y) == ty
            for unit in gameplay_state.units + gameplay_state.enemy_units
        ):
            return False
        if not allow_resources and any(int(res.x) == tx and int(res.y) == ty for res in gameplay_state.resources):
            return False
        return True

    def get_build_sites(self, building_type, builder, gameplay_state, reserved_build_tiles):
        builder_tile = (int(builder.x), int(builder.y))
        candidate_tiles = set()

        if building_type == "town_centre":
            if self.can_build_town_centre(*builder_tile, gameplay_state, min_distance=10):
                candidate_tiles.add(builder_tile)
        elif building_type == "barracks":
            for building in gameplay_state.e_buildings:
                if building.type != "town_centre":
                    continue
                x, y = int(building.x), int(building.y)
                candidate_tiles.update(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
        elif building_type in ("mill", "gold_mine"):
            resource_type = "food" if building_type == "mill" else "gold"
            for resource in gameplay_state.resources:
                site = (int(resource.x), int(resource.y))
                if (resource.resource_type == resource_type and not resource.building
                        and not resource.is_depleted()
                        and self.is_build_site_available(*site, builder, gameplay_state,
                                                         reserved_build_tiles, allow_resources=True)):
                    candidate_tiles.add(site)
        elif building_type == "farm":
            for building in gameplay_state.e_buildings:
                if building.type == "mill":
                    x, y = int(building.x), int(building.y)
                    candidate_tiles.update(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))

        return sorted(
            (
                site for site in candidate_tiles
                if self.is_build_site_available(
                    *site, builder, gameplay_state, reserved_build_tiles,
                    allow_resources=building_type in ("mill", "gold_mine")
                )
            ),
            key=lambda site: abs(builder_tile[0] - site[0]) + abs(builder_tile[1] - site[1])
        )

    # Checks if the AI's target tile is far enough away from any existing Enemy Town Centre
    def can_build_town_centre(self, tx, ty, gameplay_state, min_distance=10):
        for b in gameplay_state.e_buildings:
            if b.type == "town_centre":
                bx, by = int(b.x), int(b.y)
                if math.hypot(tx - bx, ty - by) < min_distance:
                    return False
        return True

    def find_adjacent_town_centre_tile(self, gameplay_state):
        for building in gameplay_state.e_buildings:
            if building.type != "town_centre":
                continue

            x, y = int(building.x), int(building.y)
            for tile in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                tx, ty = tile
                if not (0 <= tx < PLAYABLE_WIDTH and 0 <= ty < PLAYABLE_HEIGHT):
                    continue
                occupied = any(int(unit.x) == tx and int(unit.y) == ty for unit in gameplay_state.units)
                occupied |= any(int(unit.x) == tx and int(unit.y) == ty for unit in gameplay_state.enemy_units)
                occupied |= any(int(item.x) == tx and int(item.y) == ty for item in gameplay_state.buildings)
                occupied |= any(int(item.x) == tx and int(item.y) == ty for item in gameplay_state.e_buildings)
                occupied |= any(int(item.x) == tx and int(item.y) == ty for item in gameplay_state.resources)
                if not occupied:
                    return tile
        return None

    # Checks if a tile is adjacent to any Mill owned by the enemy
    def is_adjacent_to_mill(self, tx, ty, gameplay_state):
        neighbors = [(tx-1, ty), (tx+1, ty), (tx, ty-1), (tx, ty+1)]
        for b in gameplay_state.e_buildings:
            if b.type == "mill" and (int(b.x), int(b.y)) in neighbors:
                return True
        return False
    
    # Train enemy units by checking each building's trainable units, filtering them based on affordability and 
    # specific rules, and spawning them if possible.
    def train_enemy_units(self, game_state):
        current_villagers = sum(
            getattr(unit, "type", "") == "villager" for unit in game_state.enemy_units
        )
        current_military = sum(
            getattr(unit, "type", "") != "villager" and unit.health > 0
            for unit in game_state.enemy_units
        )
        villager_limit = 5
        military_limit = self.military_goals.get(game_state.enemy_age, {}).get("units")
        unit_configs = game_state.get_faction_units(game_state.enemy_faction)

        for building in game_state.e_buildings:
            if not building.is_constructed:
                continue

            building_data = game_state.get_building_data(
                building.type, game_state.enemy_faction
            )
            if not building_data:
                continue

            spawn_x, spawn_y = building.x, building.y
            spawn_blocked = any(
                int(unit.x) == spawn_x and int(unit.y) == spawn_y
                for unit in game_state.enemy_units
            )
            if spawn_blocked:
                continue

            affordable_units = []
            for unit_name in building_data.get("trainable units", []):
                unit_key = unit_name.lower()
                if unit_key == "villager":
                    if "town" not in building.type.lower() or current_villagers >= villager_limit:
                        continue
                elif military_limit is not None and current_military >= military_limit:
                    continue

                unit_data = unit_configs.get(unit_key)
                if not unit_data:
                    continue
                costs = unit_data["cost"]
                if (game_state.enemy_food >= costs["food"]
                        and game_state.enemy_wood >= costs["wood"]
                        and game_state.enemy_gold >= costs["gold"]):
                    affordable_units.append((unit_key, unit_data))

            if not affordable_units:
                continue

            unit_name, unit_data = random.choice(affordable_units)
            costs = unit_data["cost"]
            stats = unit_data["stats"]
            new_unit = BaseUnits(
                spawn_x, spawn_y, stats["movement"], stats["attack"],
                stats["defense"], stats.get("range", 1),
                type=unit_name, loyalty="enemy"
            )
            new_unit.unit_queued()
            game_state.enemy_units.append(new_unit)
            game_state.enemy_food -= costs["food"]
            game_state.enemy_wood -= costs["wood"]
            game_state.enemy_gold -= costs["gold"]

            if unit_name == "villager":
                current_villagers += 1
            else:
                current_military += 1

            building.rest()
            print(f"Enemy spawns: {unit_name} at ({spawn_x}, {spawn_y})")