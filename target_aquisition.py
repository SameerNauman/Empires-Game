class TargetAquisition():
    def __init__(self):
        pass

    def is_enemy_adjacent(self, selected_tile, enemy_units):
        adjacent_offsets = [
        (-1, 0),  # Top-left
        (0, -1),  # Top-right
        (0, 1),   # Bottom-left
        (1, 0)    # Bottom-right
        ]

        # Check each adjacent tile
        for dx, dy in adjacent_offsets:
            adjacent_x = selected_tile[0] + dx
            adjacent_y = selected_tile[1] + dy

            # Check if any enemy unit is on this tile
            for enemy in enemy_units:
                if enemy.x == adjacent_x and enemy.y == adjacent_y:
                    return True  # Enemy found

        return False  # No enemy adjacent
    
    def adjacent_enemy(self, selected_tile, enemy_units):
        adjacent_offsets = [
        (-1, 0),  # Top-left
        (0, -1),  # Top-right
        (0, 1),   # Bottom-left
        (1, 0)    # Bottom-right
        ]

        # Check each adjacent tile
        for dx, dy in adjacent_offsets:
            adjacent_x = selected_tile[0] + dx
            adjacent_y = selected_tile[1] + dy

            # Check if any enemy unit is on this tile
            for enemy in enemy_units:
                if enemy.x == adjacent_x and enemy.y == adjacent_y:
                    return enemy
                
    def ranged_enemy(self, selected_tile, attack_range, enemy_units):
        tx, ty = selected_tile
        for enemy in enemy_units:
            dist = abs(enemy.x - tx) + abs(enemy.y - ty)
            if 1 < dist <= attack_range:  # not adjacent, but within range
                return enemy
        return None

    def any_ranged_enemy_in_range(self, selected_tile, attack_range, enemy_units):
        tx, ty = selected_tile
        for enemy in enemy_units:
            dist = abs(enemy.x - tx) + abs(enemy.y - ty)
            if 1 < dist <= attack_range:
                return True
        return False
    
    def all_ranged_enemies(self, pos, attack_range, enemy_units):
        # Returns all enemy units in range
        tx, ty = pos
        return [
            e for e in enemy_units
            if abs(int(e.x) - tx) + abs(int(e.y) - ty) <= attack_range
        ]
    
    def all_adjacent_enemies(self, pos, enemy_units):
        tx, ty = pos
        return [
            e for e in enemy_units
            if abs(int(e.x) - tx) + abs(int(e.y) - ty) == 1
        ]
    
    def all_ranged_buildings(self, pos, attack_range, enemy_buildings):
        tx, ty = pos
        return [
            b for b in enemy_buildings
            if abs(int(b.x) - tx) + abs(int(b.y) - ty) <= attack_range
        ]

    def all_adjacent_buildings(self, pos, enemy_buildings):
        tx, ty = pos
        return [
            b for b in enemy_buildings
            if abs(int(b.x) - tx) + abs(int(b.y) - ty) == 1
        ]
