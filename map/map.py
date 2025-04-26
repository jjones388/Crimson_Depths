import numpy as np
import random
from config import TileType, MAP_WIDTH, MAP_HEIGHT, MAX_ROOMS, MIN_ROOM_SIZE, MAX_ROOM_SIZE
from .room import Room
import heapq

class Map:
    def __init__(self, width, height, level=1):
        self.width = width
        self.height = height
        self.level = level  # Dungeon level number
        self.tiles = np.full((height, width), TileType.WALL, dtype=object)
        self.rooms = []
        self.entities = []
        # FOV properties
        self.visible = np.full((height, width), False, dtype=bool)
        self.explored = np.full((height, width), False, dtype=bool)
        # Stairs positions
        self.up_stairs_position = None
        self.down_stairs_position = None
    
    def create_room(self, room):
        # Make the tiles in a room passable
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                self.tiles[y][x] = TileType.FLOOR
    
    def create_h_tunnel(self, x1, x2, y):
        # Create a horizontal tunnel
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[y][x] = TileType.CORRIDOR
    
    def create_v_tunnel(self, y1, y2, x):
        # Create a vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[y][x] = TileType.CORRIDOR
    
    def is_blocked(self, x, y):
        # First test the map tile
        if self.tiles[y][x] in [TileType.WALL, TileType.TOWN_WALL]:
            return True
        
        # Now check for any blocking entities
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return True
        
        return False
    
    def get_unexplored_tiles(self, explored_only=False):
        """Returns a list of unexplored tiles that are adjacent to explored tiles"""
        frontier_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                # Only consider floor and corridor tiles 
                if self.tiles[y][x] in [TileType.FLOOR, TileType.CORRIDOR, TileType.STAIRS_DOWN, TileType.STAIRS_UP]:
                    # If we only want unexplored tiles adjacent to explored tiles
                    if explored_only:
                        if not self.explored[y][x]:
                            # Check if adjacent to any explored tiles
                            is_adjacent_to_explored = False
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                                nx, ny = x + dx, y + dy
                                if (0 <= nx < self.width and 0 <= ny < self.height and 
                                    self.explored[ny][nx] and not self.is_blocked(nx, ny)):
                                    is_adjacent_to_explored = True
                                    break
                            if is_adjacent_to_explored:
                                frontier_tiles.append((x, y))
                    # If we want all unexplored tiles
                    elif not self.explored[y][x]:
                        frontier_tiles.append((x, y))
        return frontier_tiles
    
    def get_path(self, start_x, start_y, target_x, target_y):
        """A* pathfinding algorithm to find a path from start to target"""
        # Define the heuristic (Manhattan distance)
        def heuristic(x, y):
            return abs(x - target_x) + abs(y - target_y)
        
        # Define possible movements (including diagonals)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        
        # Priority queue for A*
        frontier = []
        heapq.heappush(frontier, (0, (start_x, start_y)))
        
        # Dict to track where we came from
        came_from = {(start_x, start_y): None}
        
        # Dict to track the cost to reach each position
        cost_so_far = {(start_x, start_y): 0}
        
        while frontier:
            _, current = heapq.heappop(frontier)
            current_x, current_y = current
            
            # If we reached the goal
            if current_x == target_x and current_y == target_y:
                break
            
            for dx, dy in directions:
                next_x, next_y = current_x + dx, current_y + dy
                
                # Check if the next position is valid
                if not (0 <= next_x < self.width and 0 <= next_y < self.height):
                    continue
                    
                # Check if the next position is blocked
                if self.is_blocked(next_x, next_y):
                    continue
                
                # Calculate the cost to move to the next position (diagonal moves cost more)
                movement_cost = 1.0 if dx == 0 or dy == 0 else 1.4
                new_cost = cost_so_far[current] + movement_cost
                
                # If we haven't been here before or found a better path
                if (next_x, next_y) not in cost_so_far or new_cost < cost_so_far[(next_x, next_y)]:
                    cost_so_far[(next_x, next_y)] = new_cost
                    priority = new_cost + heuristic(next_x, next_y)
                    heapq.heappush(frontier, (priority, (next_x, next_y)))
                    came_from[(next_x, next_y)] = current
        
        # Reconstruct the path
        if (target_x, target_y) not in came_from:
            return []  # No path found
            
        path = []
        current = (target_x, target_y)
        while current != (start_x, start_y):
            path.append(current)
            current = came_from[current]
        
        # Reverse the path to get from start to end
        path.reverse()
        return path
    
    def generate(self):
        # Generate a dungeon map
        for r in range(MAX_ROOMS):
            # Random width and height
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            # Random position without going out of the boundaries of the map
            x = random.randint(0, self.width - w - 1)
            y = random.randint(0, self.height - h - 1)
            
            new_room = Room(x, y, w, h)
            
            # Check if the room intersects with existing rooms
            if any(new_room.intersects(other_room) for other_room in self.rooms):
                continue  # This room intersects, so we'll ignore it
            
            # It's valid, so add it to the map
            self.create_room(new_room)
            
            # Connect to previous room
            if self.rooms:
                # Center coordinates of previous room
                prev_x, prev_y = self.rooms[-1].center_x, self.rooms[-1].center_y
                
                # Center coordinates of this room
                new_x, new_y = new_room.center_x, new_room.center_y
                
                # 50% chance of going horizontal first, then vertical
                if random.random() < 0.5:
                    self.create_h_tunnel(prev_x, new_x, prev_y)
                    self.create_v_tunnel(prev_y, new_y, new_x)
                else:
                    self.create_v_tunnel(prev_y, new_y, prev_x)
                    self.create_h_tunnel(prev_x, new_x, new_y)
            
            self.rooms.append(new_room)
