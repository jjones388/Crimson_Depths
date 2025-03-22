from ...config import ItemType, YELLOW, GREEN, RED, LIGHT_BLUE

class Item:
    def __init__(self, use_function=None, item_type=ItemType.MISC, equippable=False, ac_bonus=0, damage_dice=None, weapon_data=None):
        self.use_function = use_function
        self.owner = None
        self.item_type = item_type
        self.equippable = equippable
        self.ac_bonus = ac_bonus  # AC bonus provided by armor
        self.damage_dice = damage_dice  # Damage dice for weapons (n, sides)
        self.weapon_data = weapon_data  # WeaponData instance for weapons
        
    def use(self, player, message_log, entities):
        # For consumable items
        if self.use_function is not None:
            if self.use_function(player, message_log):
                # Remove the item from inventory after successful use
                player.inventory.remove_item(self.owner)
                return True
            return False
        
        # For equippable items
        elif self.equippable:
            from ...config import EquipmentSlot
            
            slot = self.get_slot()
            if slot is None:
                message_log.add_message(f"The {self.owner.name} cannot be equipped.", YELLOW)
                return False
                
            if player.inventory.get_equipped_item(slot) == self.owner:
                # Item is already equipped, unequip it
                player.inventory.unequip_item(slot, message_log, entities)
            else:
                # Equip the item
                player.inventory.equip_item(self.owner, slot, message_log, entities)
            return True
        
        # Can't use this item
        message_log.add_message(f"The {self.owner.name} cannot be used.", YELLOW)
        return False
    
    def get_slot(self):
        # Map item types to equipment slots
        from ...config import EquipmentSlot
        
        if self.item_type == ItemType.WEAPON:
            return EquipmentSlot.RIGHT_HAND
        elif self.item_type == ItemType.SHIELD:
            return EquipmentSlot.LEFT_HAND
        elif self.item_type == ItemType.HELMET:
            return EquipmentSlot.HEAD
        elif self.item_type == ItemType.ARMOR:
            return EquipmentSlot.TORSO
        elif self.item_type == ItemType.LEG_ARMOR:
            return EquipmentSlot.LEGS
        elif self.item_type == ItemType.GLOVES:
            return EquipmentSlot.HANDS
        elif self.item_type == ItemType.BOOTS:
            return EquipmentSlot.FEET
        return None

def heal_player(player, message_log):
    # Healing potion effect
    if player.fighter.hp == player.fighter.max_hp:
        message_log.add_message("You're already at full health!", YELLOW)
        return False  # No healing needed
    
    heal_amount = 10
    player.fighter.hp = min(player.fighter.hp + heal_amount, player.fighter.max_hp)
    message_log.add_message(f"You consume the healing potion and recover {heal_amount} HP.", GREEN)
    return True
