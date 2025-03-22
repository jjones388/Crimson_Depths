import numpy as np
import random
from ..config import TileType, MAP_WIDTH, MAP_HEIGHT, MAX_ROOMS, MIN_ROOM_SIZE, MAX_ROOM_SIZE
from .room import Room

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
        if self.tiles[y][x] == TileType.WALL:
            return True
        
        # Now check for any blocking entities
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return True
        
        return False
    
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
