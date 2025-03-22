import random
from ..map.map import Map
from ..data.items import place_entities
from ..config import MAP_WIDTH, MAP_HEIGHT, MAX_ENEMIES_PER_ROOM, MAX_ITEMS_PER_ROOM, TileType, EntityType

class GameWorld:
    def __init__(self, max_levels=20):
        self.max_levels = max_levels
        self.levels = {}
        self.current_level = 1
        # Set a single seed for the entire dungeon
        self.seed = random.randint(0, 1000000)
    
    def initialize_level(self, level_number):
        """Create a new level if it doesn't already exist"""
        if level_number not in self.levels:
            # Set the random seed for consistent generation
            level_seed = self.seed + level_number  # Unique seed for each level
            random.seed(level_seed)
            
            # Create the new dungeon level
            game_map = Map(MAP_WIDTH, MAP_HEIGHT, level_number)
            game_map.generate()
            
            # Create list for level entities (excluding player)
            entities = []
            
            # Place entities in the map
            for room in game_map.rooms[1:]:
                place_entities(room, entities, MAX_ENEMIES_PER_ROOM, MAX_ITEMS_PER_ROOM, level_number)
            
            # Set the stairs positions
            # Down stairs in a random room (except first room where player spawns)
            if level_number < self.max_levels:
                down_stairs_room = random.choice(game_map.rooms[1:])
                game_map.tiles[down_stairs_room.center_y][down_stairs_room.center_x] = TileType.STAIRS_DOWN
                game_map.down_stairs_position = (down_stairs_room.center_x, down_stairs_room.center_y)
            
            # Up stairs in another random room
            if level_number > 1:
                up_room_candidates = [room for room in game_map.rooms if 
                                   (room.center_x, room.center_y) != getattr(game_map, 'down_stairs_position', None)]
                up_stairs_room = random.choice(up_room_candidates)
                game_map.tiles[up_stairs_room.center_y][up_stairs_room.center_x] = TileType.STAIRS_UP
                game_map.up_stairs_position = (up_stairs_room.center_x, up_stairs_room.center_y)
            
            # Store the level
            self.levels[level_number] = (game_map, entities)
            
            # Reset random seed
            random.seed()
        
        return self.levels[level_number]
    
    def get_current_level(self):
        """Get the current level map and entities"""
        return self.initialize_level(self.current_level)
    
    def go_up_stairs(self, player):
        """Move player up one level if possible"""
        if self.current_level > 1:
            # Get current game map
            current_map = self.levels[self.current_level][0]
            
            # Check if player is on up stairs
            if (current_map.tiles[player.y][player.x] == TileType.STAIRS_UP):
                self.current_level -= 1
                
                # Get the new level
                new_map, _ = self.get_current_level()
                
                # Position player at the down stairs on the upper level
                player.x, player.y = new_map.down_stairs_position
                return True
        
        return False
    
    def go_down_stairs(self, player):
        """Move player down one level if possible"""
        if self.current_level < self.max_levels:
            # Get current game map
            current_map = self.levels[self.current_level][0]
            
            # Check if player is on down stairs
            if (current_map.tiles[player.y][player.x] == TileType.STAIRS_DOWN):
                self.current_level += 1
                
                # Get the new level (initialize if needed)
                new_map, _ = self.get_current_level()
                
                # Position player at the up stairs on the lower level
                if hasattr(new_map, 'up_stairs_position'):
                    player.x, player.y = new_map.up_stairs_position
                else:
                    # Fallback to first room center if something went wrong
                    player.x, player.y = new_map.rooms[0].center_x, new_map.rooms[0].center_y
                
                return True
        
        return False
        
    def update_entities(self, entities):
        """Update the entities for the current level"""
        # Get player from entities
        player = next((e for e in entities if e.entity_type == EntityType.PLAYER), None)
        
        if player:
            # Remove player from entities to store
            entities_without_player = [e for e in entities if e.entity_type != EntityType.PLAYER]
            
            # Store the updated entities
            current_map = self.levels[self.current_level][0]
            self.levels[self.current_level] = (current_map, entities_without_player)
