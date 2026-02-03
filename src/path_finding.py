import heapq
from collections import deque
from config import *

class PathFinding:
    def __init__(self, player_units, enemy_units, player_buildings=None, enemy_buildings=None, moving_side='player'):
        self.player_units = player_units  # list of friendly units
        self.enemy_units = enemy_units    # list of enemy units
        self.player_buildings = player_buildings if player_buildings is not None else []
        self.enemy_buildings = enemy_buildings if enemy_buildings is not None else []
        self.moving_side = moving_side  # 'player' or 'enemy'

    def is_player_building(self, x, y):
        return any(int(b.x) == x and int(b.y) == y and getattr(b, 'is_constructed', True) and getattr(b, 'hitpoints', 1) > 0 for b in self.player_buildings)

    def is_enemy_building(self, x, y):
        return any(int(b.x) == x and int(b.y) == y and getattr(b, 'is_constructed', True) and getattr(b, 'hitpoints', 1) > 0 for b in self.enemy_buildings)

    def is_enemy(self, x, y):
        return any(int(enemy.x) == x and int(enemy.y) == y for enemy in self.enemy_units)

    def is_friendly(self, x, y):
        return any(int(unit.x) == x and int(unit.y) == y for unit in self.player_units)

    def neighbors(self, x, y):
        # Only return neighbors that are inside the map and passable
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            # Defensive bounds check
            if 0 <= nx < len(PLAYABLE_MAP) and 0 <= ny < len(PLAYABLE_MAP[nx]):
                tile = PLAYABLE_MAP[nx][ny]
                if tile not in TILE_TYPES or TILE_TYPES[tile] is None:
                    continue
                # Player units cannot step on enemy buildings
                if self.moving_side == 'player' and self.is_enemy_building(nx, ny):
                    continue
                # Enemy units cannot step on player buildings
                if self.moving_side == 'enemy' and self.is_player_building(nx, ny):
                    continue
                yield nx, ny

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_star(self, start, goal, max_cost):
        heap = [(0, start)]
        came_from = {}
        cost_so_far = {start: 0}
        while heap:
            _, current = heapq.heappop(heap)
            if current == goal:
                break
            for neighbor in self.neighbors(*current):
                x, y = neighbor
                # ENEMY-occupied tiles cannot be entered (unless it's the goal)
                if self.is_enemy(x, y) and neighbor != goal:
                    continue
                # FRIENDLY-occupied tiles cannot be entered (unless it's the goal)
                if self.is_friendly(x, y) and neighbor != goal:
                    continue
                tile = PLAYABLE_MAP[x][y]
                tile_cost = TILE_TYPES.get(tile)
                if tile_cost is None:
                    continue
                new_cost = cost_so_far[current] + tile_cost
                if new_cost > max_cost:
                    continue
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(goal, neighbor)
                    heapq.heappush(heap, (priority, neighbor))
                    came_from[neighbor] = current
        # Path reconstruction
        path = []
        current = goal
        if current not in came_from and current != start:
            return []  # No path found
        while current != start:
            if current not in came_from:
                return []
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path
        
    def bfs_reachable(self, start, max_cost):
        visited = set()
        queue = deque([(start, 0)])
        reachable = set()
        while queue:
            current, cost = queue.popleft()
            x, y = current
            if current in visited:
                continue
            visited.add(current)
            # Only add to reachable if you can stop here (not occupied by a friendly, unless it's the start)
            if current == start or not self.is_friendly(x, y):
                reachable.add(current)
            for neighbor in self.neighbors(x, y):
                nx, ny = neighbor
                # ENEMY-occupied tiles cannot be entered
                if self.is_enemy(nx, ny):
                    continue
                # FRIENDLY-occupied tiles cannot be entered (except for start)
                if self.is_friendly(nx, ny) and (nx, ny) != start:
                    continue
                tile = PLAYABLE_MAP[nx][ny]
                tile_cost = TILE_TYPES.get(tile)
                if tile_cost is None:
                    continue
                new_cost = cost + tile_cost
                if new_cost > max_cost:
                    continue
                queue.append((neighbor, new_cost))
        return reachable