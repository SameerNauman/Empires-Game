from path_finding import PathFinding

class EnemyAi():
    def __init__(self, path_enemies):
        self.path_finding = PathFinding(path_enemies)

    def plan_enemy_paths(self, enemy_units, player_units, player_buildings):
        """
        For each enemy, plan their path to the nearest player unit or building (do not move yet).
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

            # Find path to target
            path = self.path_finding.a_star(
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
                    player.health -= enemy.attack
                    print(f"Enemy at ({enemy.x},{enemy.y}) attacks player at ({player.x},{player.y})!")
                    if player.health <= 0:
                        print(f"Player at ({player.x},{player.y}) is defeated!")
                        player_units.remove(player)
                    break  # Only one attack per turn

            # Attack adjacent player buildings (constructed and not destroyed)
            for building in player_buildings:
                if getattr(building, 'is_constructed', True) and getattr(building, 'hitpoints', 1) > 0:
                    if abs(enemy.x - building.x) + abs(enemy.y - building.y) == 1:
                        building.hitpoints -= enemy.attack
                        print(f"Enemy at ({enemy.x},{enemy.y}) attacks building at ({building.x},{building.y})!")
                        if building.hitpoints <= 0:
                            print(f"Building at ({building.x},{building.y}) is destroyed!")
                            player_buildings.remove(building)
                        break  # Only one attack per turn