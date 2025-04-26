import math
from config import EntityType, RED

class Entity:
    def __init__(self, x, y, char, color, entity_type, name, blocks=True, fighter=None, ai=None, item=None, inventory=None, silver_pieces=0):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.entity_type = entity_type
        self.name = name
        self.blocks = blocks  # Does this entity block movement?
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self
        
        self.ai = ai
        if self.ai:
            self.ai.owner = self
        
        self.item = item
        if self.item:
            self.item.owner = self
            
        self.inventory = inventory
        if self.inventory:
            self.inventory.owner = self
            
        self.silver_pieces = silver_pieces
    
    def force_move(self, new_x, new_y):
        """Force the entity to move regardless of obstacles"""
        self.x = new_x
        self.y = new_y
        if hasattr(self, 'ai') and self.ai and hasattr(self.ai, 'is_in_doorway'):
            self.ai.is_in_doorway = False
        return True
    
    def move(self, dx, dy, game_map, message_log=None):
        # Move by the given amount if not blocked
        if 0 <= self.x + dx < game_map.width and 0 <= self.y + dy < game_map.height:
            if not game_map.is_blocked(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy
                
                # Double-check we're still within bounds after all movement
                self.x = max(0, min(game_map.width - 1, self.x))
                self.y = max(0, min(game_map.height - 1, self.y))
                
                # Check for silver pickup if this is the player
                if self.entity_type == EntityType.PLAYER:
                    for entity in list(game_map.entities):
                        if entity.entity_type == EntityType.ITEM and entity.name == "Silver" and entity.x == self.x and entity.y == self.y:
                            # Add silver to player's total
                            self.silver_pieces += entity.silver_pieces
                            game_map.entities.remove(entity)
                            message_log.add_message(f"You pick up {entity.silver_pieces} silver pieces.", RED)
                            
                return True
            else:
                # First check for shopkeeper interaction (player bumping into shopkeeper)
                if self.entity_type == EntityType.PLAYER:
                    for entity in list(game_map.entities):
                        if (entity.entity_type == EntityType.ENEMY and 
                            entity.ai and 
                            hasattr(entity.ai, 'on_player_enter') and
                            entity.x == self.x + dx and entity.y == self.y + dy):
                            
                            # Give the shopkeeper a greeting message first
                            entity.ai.on_player_enter(self, message_log, game_map)
                            
                            # SUPER DIRECT APPROACH: Just move the shopkeeper one step inside the shop
                            # in a direction away from the player
                            
                            # Get the shopkeeper's current position
                            shop_x, shop_y = entity.x, entity.y
                            
                            # Calculate direction from player to shopkeeper
                            # (this is the direction the player is approaching from)
                            approach_dx = shop_x - self.x
                            approach_dy = shop_y - self.y
                            
                            # Get shop boundaries
                            x1, y1, x2, y2 = entity.ai.shop_area
                            
                            # HARDCODED SOLUTIONS based on the shop boundaries and player approach
                            # Determine possible positions the shopkeeper could move to
                            if approach_dx == 0 and approach_dy < 0:  # Player is above shopkeeper
                                print("Player approaching from NORTH")
                                # Try moving South into the shop
                                new_positions = [(shop_x, shop_y+1), (shop_x+1, shop_y+1), (shop_x-1, shop_y+1)]
                            elif approach_dx == 0 and approach_dy > 0:  # Player is below shopkeeper
                                print("Player approaching from SOUTH")
                                # Try moving North into the shop
                                new_positions = [(shop_x, shop_y-1), (shop_x+1, shop_y-1), (shop_x-1, shop_y-1)]
                            elif approach_dx < 0 and approach_dy == 0:  # Player is left of shopkeeper
                                print("Player approaching from WEST")
                                # Try moving East into the shop
                                new_positions = [(shop_x+1, shop_y), (shop_x+1, shop_y+1), (shop_x+1, shop_y-1)]
                            elif approach_dx > 0 and approach_dy == 0:  # Player is right of shopkeeper
                                print("Player approaching from EAST")
                                # Try moving West into the shop
                                new_positions = [(shop_x-1, shop_y), (shop_x-1, shop_y+1), (shop_x-1, shop_y-1)]
                            elif approach_dx < 0 and approach_dy < 0:  # Player is NW of shopkeeper
                                print("Player approaching from NW")
                                # Try SE corner
                                new_positions = [(shop_x+1, shop_y+1), (shop_x+1, shop_y), (shop_x, shop_y+1)]
                            elif approach_dx > 0 and approach_dy < 0:  # Player is NE of shopkeeper
                                print("Player approaching from NE")
                                # Try SW corner
                                new_positions = [(shop_x-1, shop_y+1), (shop_x-1, shop_y), (shop_x, shop_y+1)]
                            elif approach_dx < 0 and approach_dy > 0:  # Player is SW of shopkeeper
                                print("Player approaching from SW")
                                # Try NE corner
                                new_positions = [(shop_x+1, shop_y-1), (shop_x+1, shop_y), (shop_x, shop_y-1)]
                            elif approach_dx > 0 and approach_dy > 0:  # Player is SE of shopkeeper
                                print("Player approaching from SE")
                                # Try NW corner
                                new_positions = [(shop_x-1, shop_y-1), (shop_x-1, shop_y), (shop_x, shop_y-1)]
                            else:
                                # Default: try to move to center of shop
                                print("Unknown player approach direction")
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                new_positions = [(center_x, center_y)]
                            
                            # Try each position until we find one inside the shop
                            moved = False
                            for new_x, new_y in new_positions:
                                # Make sure position is inside shop
                                if x1 <= new_x <= x2 and y1 <= new_y <= y2:
                                    print(f"Moving shopkeeper to {new_x}, {new_y}")
                                    # Force the shopkeeper to move
                                    entity.x = new_x
                                    entity.y = new_y
                                    if hasattr(entity.ai, 'is_in_doorway'):
                                        entity.ai.is_in_doorway = False
                                    moved = True
                                    break
                            
                            # If no position worked, try shop center
                            if not moved:
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                entity.x = center_x
                                entity.y = center_y
                                if hasattr(entity.ai, 'is_in_doorway'):
                                    entity.ai.is_in_doorway = False
                                print(f"Moving shopkeeper to center: {center_x}, {center_y}")
                            
                            message_log.add_message(f"The {entity.name} steps aside.", RED)
                            return "You meet the shopkeeper."
                
                # Check for entities to attack (but not shopkeepers)
                for entity in list(game_map.entities):  # Create a copy to avoid issues with entity removal
                    if (entity.fighter and 
                        entity.x == self.x + dx and entity.y == self.y + dy and
                        not (entity.ai and hasattr(entity.ai, 'on_player_enter'))):  # Not a shopkeeper
                        if self.fighter:
                            return self.fighter.attack(entity, message_log)
        return False
