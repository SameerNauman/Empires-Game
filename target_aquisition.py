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