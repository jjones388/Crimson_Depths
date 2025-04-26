import numpy as np
import random
from config import TileType, MAP_WIDTH, MAP_HEIGHT, EntityType
from .room import Room

# Building types for the town
class BuildingType:
    WEAPONSMITH = 0
    ARMORSMITH = 1
    APOTHECARY = 2

# Building data structure
class Building:
    def __init__(self, x, y, width, height, building_type):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.center_x = (self.x1 + self.x2) // 2
        self.center_y = (self.y1 + self.y2) // 2
        self.door_x = None
        self.door_y = None
        self.building_type = building_type
        self.name = self._get_name()
    
    def _get_name(self):
        if self.building_type == BuildingType.WEAPONSMITH:
            return "Weaponsmith"
        elif self.building_type == BuildingType.ARMORSMITH:
            return "Armorsmith"
        elif self.building_type == BuildingType.APOTHECARY:
            return "Apothecary"
        return "Building"
    
    def intersects(self, other):
        # Check if this building intersects with another
        # Add a buffer of 3 tiles for spacing between buildings
        return (
            self.x1 - 3 <= other.x2 + 3 and
            self.x2 + 3 >= other.x1 - 3 and
            self.y1 - 3 <= other.y2 + 3 and
            self.y2 + 3 >= other.y1 - 3
        )
    
    def is_too_close_to_town_square(self, center_x, center_y, square_size):
        """Check if building is too close to the town square with the stairs"""
        # Add a buffer around the town square (extra tiles beyond the square itself)
        buffer_distance = 2
        square_with_buffer = square_size + buffer_distance
        
        # Check if any part of the building overlaps with the town square buffer
        return (
            self.x1 <= center_x + square_with_buffer and
            self.x2 >= center_x - square_with_buffer and
            self.y1 <= center_y + square_with_buffer and
            self.y2 >= center_y - square_with_buffer
        )

def generate_town_map(map_obj):
    """Generate a town map with buildings and grass"""
    # Fill the map with grass
    map_obj.tiles = np.full((map_obj.height, map_obj.width), TileType.GRASS, dtype=object)
    
    # Set the entire town map to explored
    map_obj.explored = np.full((map_obj.height, map_obj.width), True, dtype=bool)
    
    # Define the town square size and center
    center_x = map_obj.width // 2
    center_y = map_obj.height // 2
    town_square_size = 3  # Size from center to edge (makes a 7x7 square)
    
    # List to store buildings
    buildings = []
    
    # Generate buildings
    building_types = [
        BuildingType.WEAPONSMITH,
        BuildingType.ARMORSMITH,
        BuildingType.APOTHECARY
    ]
    
    # Place buildings at random positions
    for building_type in building_types:
        # Random width and height for each building
        width = random.randint(8, 12)
        height = random.randint(6, 8)
        
        # Try to place the building without overlapping with existing buildings or town square
        max_attempts = 100  # Increased attempts for more flexibility
        for _ in range(max_attempts):
            # Random position
            x = random.randint(5, map_obj.width - width - 5)
            y = random.randint(5, map_obj.height - height - 5)
            
            new_building = Building(x, y, width, height, building_type)
            
            # Check if the building intersects with existing buildings
            if any(new_building.intersects(other) for other in buildings):
                continue  # Try again with a new position
            
            # Check if the building is too close to the town square
            if new_building.is_too_close_to_town_square(center_x, center_y, town_square_size):
                continue  # Try again with a new position
            
            # Place the building
            buildings.append(new_building)
            
            # Create the building walls
            for build_y in range(new_building.y1, new_building.y2 + 1):
                for build_x in range(new_building.x1, new_building.x2 + 1):
                    # Check bounds
                    if 0 <= build_x < map_obj.width and 0 <= build_y < map_obj.height:
                        # Set walls around the perimeter
                        if (build_x == new_building.x1 or build_x == new_building.x2 or 
                            build_y == new_building.y1 or build_y == new_building.y2):
                            map_obj.tiles[build_y][build_x] = TileType.TOWN_WALL
                        # Set floor inside the building
                        else:
                            map_obj.tiles[build_y][build_x] = TileType.FLOOR
            
            # Create a door on a random side of the building
            sides = ["north", "east", "south", "west"]
            door_side = random.choice(sides)
            
            if door_side == "north":
                door_x = random.randint(new_building.x1 + 1, new_building.x2 - 1)
                door_y = new_building.y1
            elif door_side == "east":
                door_x = new_building.x2
                door_y = random.randint(new_building.y1 + 1, new_building.y2 - 1)
            elif door_side == "south":
                door_x = random.randint(new_building.x1 + 1, new_building.x2 - 1)
                door_y = new_building.y2
            else:  # west
                door_x = new_building.x1
                door_y = random.randint(new_building.y1 + 1, new_building.y2 - 1)
            
            # Set the door
            if 0 <= door_x < map_obj.width and 0 <= door_y < map_obj.height:
                map_obj.tiles[door_y][door_x] = TileType.FLOOR
                new_building.door_x = door_x
                new_building.door_y = door_y
            
            # Successfully placed this building, move to the next one
            break
    
    # Create a spot in the center of the town for the stairs down to the dungeon
    
    # Create a small stone platform around the stairs
    for py in range(center_y - town_square_size, center_y + town_square_size + 1):
        for px in range(center_x - town_square_size, center_x + town_square_size + 1):
            if 0 <= px < map_obj.width and 0 <= py < map_obj.height:
                map_obj.tiles[py][px] = TileType.FLOOR
    
    # Place the stairs in the center
    map_obj.tiles[center_y][center_x] = TileType.STAIRS_DOWN
    map_obj.down_stairs_position = (center_x, center_y)
    
    # Save the buildings in the map object for interaction
    map_obj.buildings = buildings
    
    # List of entities to return
    entities = []
    
    # Add shopkeepers and shop items
    for building in buildings:
        # Define shop boundaries for AI
        shop_area = (building.x1 + 1, building.y1 + 1, building.x2 - 1, building.y2 - 1)
        
        # Add shopkeeper at door position
        from entities.entity import Entity
        from entities.components.fighter import Fighter
        from entities.components.ai import ShopkeeperAI
        from config import WHITE
        
        # Define shopkeeper character based on shop type
        shopkeeper_char = '1'  # Default
        if building.building_type == BuildingType.WEAPONSMITH:
            shopkeeper_char = '1'
            shopkeeper_name = "Weaponsmith"
        elif building.building_type == BuildingType.ARMORSMITH:
            shopkeeper_char = '2'
            shopkeeper_name = "Armorsmith"
        elif building.building_type == BuildingType.APOTHECARY:
            shopkeeper_char = '3'
            shopkeeper_name = "Apothecary"
        
        # Create shopkeeper
        shopkeeper_ai = ShopkeeperAI(
            building.building_type, 
            building.door_x, 
            building.door_y,
            shop_area
        )
        
        shopkeeper_fighter = Fighter(hp=20, armor=2, damage_dice=(1, 6))
        # Set moderate dodge for shopkeeper
        shopkeeper_fighter.dodge = 15
        
        shopkeeper = Entity(
            building.door_x, 
            building.door_y, 
            shopkeeper_char, 
            WHITE, 
            EntityType.ENEMY, 
            shopkeeper_name,
            blocks=True,
            fighter=shopkeeper_fighter,
            ai=shopkeeper_ai
        )
        
        entities.append(shopkeeper)
        
        # Add shop items
        from data.items import create_item, ITEM_PRICES
        
        # Generate 3-6 random items appropriate for the shop type
        num_items = random.randint(3, 6)
        
        # Available item types based on shop type
        if building.building_type == BuildingType.WEAPONSMITH:
            available_items = [
                "dagger", "shortsword", "longsword", "mace", 
                "battleaxe", "warhammer", "shortbow", "longbow", "arrows"
            ]
        elif building.building_type == BuildingType.ARMORSMITH:
            available_items = [
                "leather_armor", "chainmail", "plate_armor", 
                "helmet", "boots", "gloves", "shield"
            ]
        elif building.building_type == BuildingType.APOTHECARY:
            available_items = ["healing_potion"] * 6  # Multiple entries to ensure we get enough
        
        # Place items at random positions inside the shop
        for _ in range(num_items):
            if not available_items:
                break
                
            # Choose random item from available items
            item_name = random.choice(available_items)
            available_items.remove(item_name)
            
            # Choose random position inside shop
            item_x = random.randint(building.x1 + 1, building.x2 - 1)
            item_y = random.randint(building.y1 + 1, building.y2 - 1)
            
            # Create the item
            item = create_item(item_name, item_x, item_y)
            
            # Only process successfully created items
            if item:
                # Mark as unpaid shop item and set price
                if item_name in ITEM_PRICES:
                    item.item.unpaid = True
                    item.item.price = ITEM_PRICES[item_name]
                
                entities.append(item)
    
    return entities 

# Helper function to force move a shopkeeper
def force_shopkeeper_aside(shopkeeper, game_map):
    """Force a shopkeeper to move aside from the doorway"""
    # Get shop boundaries and door position
    x1, y1, x2, y2 = shopkeeper.ai.shop_area
    door_x, door_y = shopkeeper.ai.door_x, shopkeeper.ai.door_y
    
    # Get shop dimensions and center
    shop_width = x2 - x1
    shop_height = y2 - y1
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    
    print(f"Shop boundaries: ({x1}, {y1}) to ({x2}, {y2})")
    print(f"Door position: ({door_x}, {door_y})")
    
    # If the door is outside the shop boundaries, we need a special approach
    if door_x < x1 or door_x > x2 or door_y < y1 or door_y > y2:
        print(f"Door is outside shop boundaries!")
        
        # Calculate vector from door to shop center
        dx = center_x - door_x
        dy = center_y - door_y
        
        # Normalize to get direction
        dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        # Simply move one tile toward the center of the shop
        new_x = door_x + dx
        new_y = door_y + dy
        
        print(f"Moving toward center at ({new_x}, {new_y})")
        
        # Make sure we're inside the shop - adjust if needed
        new_x = max(x1, min(x2, new_x))
        new_y = max(y1, min(y2, new_y))
        
        # Force the move
        shopkeeper.x = new_x
        shopkeeper.y = new_y
        shopkeeper.ai.is_in_doorway = False
        print(f"Moving shopkeeper to ({new_x}, {new_y})")
        return True
    
    # Try all positions around the door
    # Order them by proximity to shop center
    positions = []
    
    # Generate all adjacent positions
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue  # Skip the door position itself
                
            new_x = door_x + dx
            new_y = door_y + dy
            
            # Check if position is inside the shop
            if x1 <= new_x <= x2 and y1 <= new_y <= y2:
                # Calculate distance to shop center
                distance = abs(new_x - center_x) + abs(new_y - center_y)
                positions.append((new_x, new_y, distance))
    
    # Sort positions by distance to center (to prefer positions that move deeper into the shop)
    positions.sort(key=lambda pos: pos[2])
    
    # Try each position
    for new_x, new_y, _ in positions:
        print(f"Trying position: ({new_x}, {new_y})")
        
        # Force shopkeeper to move
        shopkeeper.x = new_x
        shopkeeper.y = new_y
        shopkeeper.ai.is_in_doorway = False
        print(f"Moving shopkeeper to ({new_x}, {new_y})")
        return True
    
    # If no positions are valid (should never happen), move to center
    print(f"No valid positions found. Moving to center ({center_x}, {center_y})")
    shopkeeper.x = center_x
    shopkeeper.y = center_y
    shopkeeper.ai.is_in_doorway = False
    return True 