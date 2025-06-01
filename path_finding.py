import heapq
from collections import deque
from config import *

class PathFinding():
    def __init__(self, player_units, enemy_units):
        self.player_units = player_units  # list of friendly units
        self.enemy_units = enemy_units    # list of enemy units

    def is_enemy(self, x, y):
        return any(enemy.x == x and enemy.y == y for enemy in self.enemy_units)

    def is_friendly(self, x, y):
        return any(unit.x == x and unit.y == y for unit in self.player_units)

    def neighbors(self, x, y):
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < PLAYABLE_WIDTH and 0 <= ny < PLAYABLE_HEIGHT:
                if TILE_TYPES[PLAYABLE_MAP[nx][ny]] is not None:
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
                # Enemy-occupied tiles cannot be entered
                if self.is_enemy(x, y):
                    continue

                tile_cost = TILE_TYPES[PLAYABLE_MAP[x][y]]
                new_cost = cost_so_far[current] + tile_cost

                if new_cost > max_cost:
                    continue

                # Don't allow stopping on a friendly-occupied tile (unless it's the goal)
                if self.is_friendly(x, y) and neighbor != goal:
                    # Can pass through, but not stop, so enqueue as normal
                    pass

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(goal, neighbor)
                    heapq.heappush(heap, (priority, neighbor))
                    came_from[neighbor] = current

        # Path reconstruction (same as before)
        path = []
        current = goal
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
                # Enemy-occupied tiles cannot be entered
                if self.is_enemy(nx, ny):
                    continue

                tile_cost = TILE_TYPES[PLAYABLE_MAP[nx][ny]]
                new_cost = cost + tile_cost
                if new_cost > max_cost:
                    continue

                # Friendly-occupied tiles can be traversed but not stopped on,
                # so always enqueue as long as not already visited.
                queue.append((neighbor, new_cost))
                
        return reachable
