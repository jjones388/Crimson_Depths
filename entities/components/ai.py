import random
from config import EntityType, LIGHT_BLUE, YELLOW
from map.town import BuildingType
from map.town import force_shopkeeper_aside

class BasicMonster:
    def __init__(self):
        self.owner = None
    
    def take_turn(self, player, game_map, message_log):
        monster = self.owner
        
        # Only take a turn if monster is visible
        if game_map.visible[monster.y][monster.x]:
            # Check if monster is adjacent to the player
            if abs(monster.x - player.x) <= 1 and abs(monster.y - player.y) <= 1:
                # Monster is adjacent to player, attack!
                if monster.fighter:
                    attack_message = monster.fighter.attack(player, message_log)
                    if attack_message:
                        message_log.add_message(str(attack_message))
            else:
                # Basic pathfinding - move towards player
                dx = player.x - monster.x
                dy = player.y - monster.y
                distance = max(abs(dx), abs(dy))
                
                if distance > 0:
                    dx = int(round(dx / distance))
                    dy = int(round(dy / distance))
                    
                    # Don't move onto stairs
                    new_x, new_y = monster.x + dx, monster.y + dy
                    if (0 <= new_x < game_map.width and 0 <= new_y < game_map.height and
                        game_map.tiles[new_y][new_x] not in 
                        [game_map.tiles[new_y][new_x].__class__.STAIRS_UP, 
                         game_map.tiles[new_y][new_x].__class__.STAIRS_DOWN, 
                         game_map.tiles[new_y][new_x].__class__.WALL] and
                        not game_map.is_blocked(new_x, new_y)):
                        monster.move(dx, dy, game_map, message_log)

class ShopkeeperAI:
    def __init__(self, shop_type, door_x, door_y, shop_area):
        self.owner = None
        self.shop_type = shop_type  # WEAPONSMITH, ARMORSMITH, or APOTHECARY
        self.door_x = door_x  # X coordinate of the shop door
        self.door_y = door_y  # Y coordinate of the shop door
        self.shop_area = shop_area  # (x1, y1, x2, y2) - shop boundaries
        self.blocking_door = True  # Starts by blocking the doorway
        self.is_in_doorway = True  # Whether shopkeeper is currently in doorway
        
    def take_turn(self, player, game_map, message_log):
        shopkeeper = self.owner
        
        # Only act if the shopkeeper is visible
        if game_map.visible[shopkeeper.y][shopkeeper.x]:
            # Define shop boundaries
            x1, y1, x2, y2 = self.shop_area
            
            # Check if player is inside the shop
            player_in_shop = (
                x1 <= player.x <= x2 and
                y1 <= player.y <= y2
            )
            
            # Check for items on shop floor
            items_on_floor = []
            for entity in game_map.entities:
                if (entity.entity_type == EntityType.ITEM and 
                    x1 <= entity.x <= x2 and 
                    y1 <= entity.y <= y2):
                    items_on_floor.append(entity)
            
            # Check if player has unpaid items
            player_has_unpaid_items = player.inventory and player.inventory.has_unpaid_items()
            
            # Decide shopkeeper behavior based on conditions
            if player_in_shop:
                # Player is in shop - check if they have unpaid items
                if player_has_unpaid_items:
                    # Move to block the door ONLY if not already moved by the player interaction
                    if not self.is_in_doorway and not (
                        # Check if the shopkeeper was recently moved by a player action
                        shopkeeper.x != self.door_x or shopkeeper.y != self.door_y
                    ):
                        shopkeeper.x = self.door_x
                        shopkeeper.y = self.door_y
                        self.is_in_doorway = True
                        message_log.add_message(f"The {shopkeeper.name} moves to block the exit.", LIGHT_BLUE)
                # Don't make the shopkeeper move back to the door automatically if player has no unpaid items
            else:
                # Player is outside shop
                # Only move back to doorway if shopkeeper is inside shop and not already at the door
                if (not self.is_in_doorway and 
                    shopkeeper.x >= x1 and shopkeeper.x <= x2 and 
                    shopkeeper.y >= y1 and shopkeeper.y <= y2):
                    shopkeeper.x = self.door_x
                    shopkeeper.y = self.door_y
                    self.is_in_doorway = True
    
    def on_player_enter(self, player, message_log, game_map):
        """Called when player enters the shop"""
        shopkeeper = self.owner
        shop_type_name = ""
        
        # Get shop type name
        if self.shop_type == BuildingType.WEAPONSMITH:
            shop_type_name = "Weaponsmith"
        elif self.shop_type == BuildingType.ARMORSMITH:
            shop_type_name = "Armorsmith"
        elif self.shop_type == BuildingType.APOTHECARY:
            shop_type_name = "Apothecary"
            
        # Welcome message
        message_log.add_message(f"Welcome to the {shop_type_name}! Items on the floor are for sale.", LIGHT_BLUE)
        
        # Always use the reliable force function instead of trying complex positioning
        force_shopkeeper_aside(shopkeeper, game_map)
        
        # Always set the flag to false since we've moved
        self.is_in_doorway = False
        
        # Confirm movement with a message
        message_log.add_message(f"The {shopkeeper.name} steps aside.", LIGHT_BLUE)
        
        return True
