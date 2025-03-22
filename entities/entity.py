from ..config import EntityType

class Entity:
    def __init__(self, x, y, char, color, entity_type, name, blocks=True, fighter=None, ai=None, item=None, inventory=None):
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
    
    def move(self, dx, dy, game_map, message_log=None):
        # Move by the given amount if not blocked
        if 0 <= self.x + dx < game_map.width and 0 <= self.y + dy < game_map.height:
            if not game_map.is_blocked(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy
                return True
            else:
                # Check for entities to attack
                for entity in list(game_map.entities):  # Create a copy to avoid issues with entity removal
                    if entity.fighter and entity.x == self.x + dx and entity.y == self.y + dy:
                        if self.fighter:
                            return self.fighter.attack(entity, message_log)
        return False
