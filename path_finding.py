import heapq
from collections import deque
from config import *

class PathFinding():
    def __init__(self, enemy_units):
        self.enemy_units = enemy_units

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
                if any(enemy.x == neighbor[0] and enemy.y == neighbor[1] for enemy in self.enemy_units):
                    continue
                tile_cost = TILE_TYPES[PLAYABLE_MAP[neighbor[0]][neighbor[1]]]
                new_cost = cost_so_far[current] + tile_cost
                
                if new_cost > max_cost:  # Respect movement range
                    continue
                    
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(goal, neighbor)
                    heapq.heappush(heap, (priority, neighbor))
                    came_from[neighbor] = current
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
            
            if current in visited:
                continue
            visited.add(current)
            
            # Only add to reachable if we can stop here
            reachable.add(current)
            
            for neighbor in self.neighbors(*current):
                # Skip tiles occupied by enemy units
                if any(enemy.x == neighbor[0] and enemy.y == neighbor[1] for enemy in self.enemy_units):
                    continue
                tile_cost = TILE_TYPES[PLAYABLE_MAP[neighbor[0]][neighbor[1]]]
                new_cost = cost + tile_cost
                if new_cost <= max_cost:
                    queue.append((neighbor, new_cost))
        
        return reachable