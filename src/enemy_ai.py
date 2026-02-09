import random
from path_finding import PathFinding
from target_aquisition import TargetAquisition
from units.base_units import BaseUnits
from config import *

class EnemyAi():
    def __init__(self, path_enemies):
        self.target_aquisition = TargetAquisition()
        # Remove the static path_finding instance; will construct per enemy on-demand.
        self.path_enemies = path_enemies

    def plan_enemy_paths(
        self, 
        enemy_units, 
        player_units, 
        player_buildings, 
        resource_list, 
        enemy_buildings=None
    ):
        """
        For each enemy, plan their path to the nearest player unit or building (do not move yet).
        Uses updated PathFinding logic: 
        - Enemy units cannot move onto or stop on tiles occupied by any unit (enemy or player).
        - Enemy units cannot walk through player buildings.
        - Player units cannot walk through enemy buildings. (handled in player code)
        """
        if enemy_buildings is None:
            enemy_buildings = []

        for enemy in enemy_units:
            if enemy.health <= 0:
                continue
    
            # --- RESOURCE GATHERING for ENEMY VILLAGERS ---
            if getattr(enemy, "type", None) == "villager":
                # Already gathering and on resource? Skip movement
                if getattr(enemy, "is_gathering", False):
                    found_res = next((r for r in resource_list if r.id == getattr(enemy, "gather_resource_id", -1)), None)
                    if found_res and (enemy.x, enemy.y) == (found_res.x, found_res.y) and not found_res.is_depleted():
                        continue

                # Find nearest non-depleted resource
                nearest_resource = None
                min_dist = float('inf')
                for res in resource_list:
                    if not res.is_depleted():
                        dist = abs(enemy.x - res.x) + abs(enemy.y - res.y)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_resource = res

                # If on resource, start gathering
                if nearest_resource and (enemy.x, enemy.y) == (nearest_resource.x, nearest_resource.y):
                    enemy.is_gathering = True
                    enemy.gather_resource_id = nearest_resource.id
                    continue

                # Otherwise, path directly to the resource tile (not adjacent!)
                if nearest_resource:
                    path_finding = PathFinding(
                        [], enemy_units, 
                        player_buildings, enemy_buildings, 
                        moving_side='enemy'
                    )
                    path = path_finding.a_star(
                        start=(int(enemy.x), int(enemy.y)),
                        goal=(int(nearest_resource.x), int(nearest_resource.y)),
                        max_cost=100
                    )
                    if path:
                        steps = min(enemy.movement_range, len(path))
                        path = path[:steps]
                        enemy.path = [(float(x), float(y)) for x, y in path]
                    else:
                        enemy.path = []
                continue  # Skip rest of logic for villagers

            # Find nearest living player unit or constructed building
            nearest_target = None
            min_dist = float('inf')

            # Search player units
            for player in player_units:
                if player.health > 0:
                    dist = abs(enemy.x - player.x) + abs(enemy.y - player.y)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_target = player

            # Search constructed player buildings
            for building in player_buildings:
                if building.hitpoints > 0:
                    dist = abs(enemy.x - building.x) + abs(enemy.y - building.y)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_target = building

            if nearest_target is None:
                enemy.path = []
                continue

            # If adjacent, don't move (attack handled later)
            if min_dist == 1:
                enemy.path = []
                continue

            # Prepare lists for pathfinding:
            # - Exclude the moving enemy from pathfinding's enemy list (so it doesn't block itself)
            # - All player units are considered as "blocking" for movement
            enemy_units_for_pathfinding = [e for e in enemy_units if e != enemy]
            player_units_for_pathfinding = player_units  # all player units

            # Create a PathFinding instance for this enemy
            path_finding = PathFinding(
                player_units_for_pathfinding, 
                enemy_units_for_pathfinding,
                player_buildings,
                enemy_buildings,
                moving_side='enemy'
            )

            # Find path to target
            path = path_finding.a_star(
                start=(int(enemy.x), int(enemy.y)),
                goal=(int(nearest_target.x), int(nearest_target.y)),
                max_cost=100
            )

            # Remove target tile from path so we don't step onto them
            if path and path[-1] == (int(nearest_target.x), int(nearest_target.y)):
                path = path[:-1]
            if path:
                steps = min(enemy.movement_range, len(path))
                path = path[:steps]
                enemy.path = [(float(x), float(y)) for x, y in path]
            else:
                enemy.path = []

    # def try_enemy_attack(self, enemy_units, player_units, player_buildings):
    #     """
    #     After movement, enemy units attack following same rules as player units:
    #     - Ranged attacks: only targets at distance > 1 and ≤ attack_range
    #     - Melee attacks: only targets at distance == 1
    #     - Units on buildings prevent the building from being targeted
    #     - Only one attack per enemy per turn
    #     """
    #     for enemy in enemy_units:
    #         if enemy.health <= 0:
    #             continue

    #         attacked = False
    #         attack_range = getattr(enemy, "attack_range", 1)

    #         # --- RANGED ATTACK (distance > 1 and ≤ attack_range) ---
    #         if attack_range > 1:
    #             # Units
    #             for player in player_units:
    #                 dist = abs(enemy.x - player.x) + abs(enemy.y - player.y)
    #                 if player.health > 0 and 1 < dist <= attack_range:
    #                     damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/player.defense) * 25 + FLAT_BONUS
    #                     player.health -= damage
    #                     self.enemy_retaliation(enemy, player, dist)
    #                     print("enemy (ranged):", enemy.health)
    #                     print("player:", player.health)
    #                     attacked = True
    #                     break
    #             if attacked:
    #                 continue
    #             # Buildings
    #             for building in player_buildings:
    #                 if getattr(building, 'is_constructed', True) and getattr(building, 'hitpoints', 1) > 0:
    #                     dist = abs(enemy.x - building.x) + abs(enemy.y - building.y)
    #                     if 1 < dist <= attack_range:
    #                         bx, by = int(building.x), int(building.y)
    #                         unit_on_building = any(
    #                             int(u.x) == bx and int(u.y) == by and u.health > 0
    #                             for u in player_units
    #                         )
    #                         if unit_on_building:
    #                             continue
    #                         damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/building.defense) * 25 + FLAT_BONUS
    #                         building.hitpoints -= enemy.attack
    #                         print("enemy (ranged):", enemy.health)
    #                         print("player building:", building.hitpoints)
    #                         attacked = True
    #                         break
    #             if attacked:
    #                 continue

    #         # --- MELEE ATTACK (distance == 1) ---
    #         # Units
    #         for player in player_units:
    #             dist = abs(enemy.x - player.x) + abs(enemy.y - player.y)
    #             if player.health > 0 and dist == 1:
    #                 damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/player.defense) * 25 + FLAT_BONUS
    #                 player.health -= damage
    #                 self.enemy_retaliation(enemy, player, dist)
    #                 print("enemy (melee):", enemy.health)
    #                 print("player:", player.health)
    #                 attacked = True
    #                 break
    #         if attacked:
    #             continue
    #         # Buildings
    #         for building in player_buildings:
    #             if getattr(building, 'is_constructed', True) and getattr(building, 'hitpoints', 1) > 0:
    #                 dist = abs(enemy.x - building.x) + abs(enemy.y - building.y)
    #                 if dist == 1:
    #                     bx, by = int(building.x), int(building.y)
    #                     unit_on_building = any(
    #                         int(u.x) == bx and int(u.y) == by and u.health > 0
    #                         for u in player_units
    #                     )
    #                     if unit_on_building:
    #                         continue
    #                     damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/building.defense) * 25 + FLAT_BONUS
    #                     building.hitpoints -= enemy.attack
    #                     print("enemy (melee):", enemy.health)
    #                     print("player building:", building.hitpoints)
    #                     break

    # Enemy unit training
    def train_enemy_units(self, e_buildings, enemy_units, gameplay_state):
        # Iterates over enemy buildings and skips over resource buildings or not constructed.
        for building in e_buildings:
            if not building.is_constructed:
                continue
            if building.type not in BUILDINGS:
                continue
            # Check if spawn location is blocked by an enemy unit
            spawn_x, spawn_y = building.x, building.y
            spawn_blocked = any(
                int(u.x) == spawn_x and int(u.y) == spawn_y for u in enemy_units
            )
            # Skip training for this building this turn
            if spawn_blocked:
                # Optionally print or log: print(f"Spawn at ({spawn_x},{spawn_y}) blocked for {building.type}")
                continue

            # Aquires building attribute list
            b_attr = BUILDINGS[building.type]
            trainable_units = b_attr[6]

            # Collect all affordable units
            affordable_units = []
            for unit_name in trainable_units:
                # Aquires unit attribute list
                u_attr = UNITS[unit_name]
                food, wood, gold = u_attr[1], u_attr[2], u_attr[3]
                if (gameplay_state.enemy_food >= food and
                    gameplay_state.enemy_wood >= wood and
                    gameplay_state.enemy_gold >= gold):
                    affordable_units.append(unit_name)

            # Randomly spawns an affordable unit
            if affordable_units:
                unit_name = random.choice(affordable_units)
                u_attr = UNITS[unit_name]
                food, wood, gold = u_attr[1], u_attr[2], u_attr[3]
                new_unit = BaseUnits(
                    spawn_x, spawn_y,
                    u_attr[5], u_attr[6], u_attr[7], u_attr[8], type=unit_name
                )
                print("Enemy spawns:", unit_name, "at", (spawn_x, spawn_y))
                enemy_units.append(new_unit)
                gameplay_state.enemy_food -= food
                gameplay_state.enemy_wood -= wood
                gameplay_state.enemy_gold -= gold
                building.rest()
                building.rest()
                # Only one unit per building per turn