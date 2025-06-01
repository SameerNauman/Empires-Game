from path_finding import PathFinding
from target_aquisition import TargetAquisition
from config import *

class EnemyAi():
    def __init__(self, path_enemies):
        self.target_aquisition = TargetAquisition()
        # Remove the static path_finding instance; will construct per enemy on-demand.
        self.path_enemies = path_enemies

    def plan_enemy_paths(self, enemy_units, player_units, player_buildings):
        """
        For each enemy, plan their path to the nearest player unit or building (do not move yet).
        Uses updated PathFinding logic: 
        - Enemy units cannot move onto or stop on tiles occupied by any unit (enemy or player).
        - Enemy units can pass through other enemy units, but not stop on their tile unless it's their own tile.
        """
        for enemy in enemy_units:
            if enemy.health <= 0:
                continue

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
                if getattr(building, 'is_constructed', True) and getattr(building, 'hitpoints', 1) > 0:
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
            path_finding = PathFinding(player_units_for_pathfinding, enemy_units_for_pathfinding)

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

    def try_enemy_attack(self, enemy_units, player_units, player_buildings):
        """
        After movement, perform attacks if adjacent to a player unit or a player building.
        """
        for enemy in enemy_units:
            if enemy.health <= 0:
                continue

            # Attack adjacent player units
            for player in list(player_units):  # copy to allow removal
                if player.health > 0 and abs(enemy.x - player.x) + abs(enemy.y - player.y) == 1:
                    damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/player.defense) * 25 + FLAT_BONUS
                    player.health -= damage
                    
                    self.enemy_retaliation(enemy, player)

                    print("enemy:", enemy.health)
                    print("player:", player.health)
                    break  # Only one attack per turn

            # Attack adjacent player buildings (constructed and not destroyed)
            for building in player_buildings:
                if getattr(building, 'is_constructed', True) and getattr(building, 'hitpoints', 1) > 0:
                    if abs(enemy.x - building.x) + abs(enemy.y - building.y) == 1:
                        damage = ((enemy.attack * (1 + BONUS_MULTIPLYER))/building.defense) * 25 + FLAT_BONUS
                        building.hitpoints -= enemy.attack
                        print("enemy:", enemy.health)
                        print("player:", building.hitpoints)
                        break  # Only one attack per turn

    def enemy_retaliation(self, attacker, defender):
        # attacker: the unit that attacked (could be player or enemy)
        # defender: the unit retaliating (could be enemy or player)
        # This works for both player->enemy and enemy->player retaliation

        # Melee retaliation (range 1)
        if getattr(defender, "attack_range", 1) == 1:
            # Only retaliate if adjacent
            if abs(attacker.x - defender.x) + abs(attacker.y - defender.y) == 1:
                damage = ((defender.attack * (1 + BONUS_MULTIPLYER)) / attacker.defense) * 25 + FLAT_BONUS
                attacker.health -= damage
        # Ranged retaliation (>1)
        else:
            dist = abs(attacker.x - defender.x) + abs(attacker.y - defender.y)
            if 1 < dist <= getattr(defender, "attack_range", 1):
                damage = ((defender.attack * (1 + BONUS_MULTIPLYER)) / attacker.defense) * 25 + FLAT_BONUS
                attacker.health -= damage
