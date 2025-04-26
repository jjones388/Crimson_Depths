from config import ItemType, YELLOW, GREEN, RED, LIGHT_BLUE, EquipmentSlot
import random

class Item:
    def __init__(self, use_function=None, item_type=None, equippable=False, 
                 armor_bonus=0, dodge_bonus=0, damage_dice=None, weapon_data=None, ammo_data=None):
        self.use_function = use_function
        self.owner = None
        self.item_type = item_type
        self.equippable = equippable
        self.armor_bonus = armor_bonus  # Damage reduction bonus provided by armor
        self.dodge_bonus = dodge_bonus  # Dodge bonus provided by equipment
        self.damage_dice = damage_dice  # Damage dice for weapons (n, sides)
        self.weapon_data = weapon_data  # WeaponData object for additional weapon info
        self.ammo_data = ammo_data      # AmmoData object for ranged weapon ammo
        
        # Shop/Economics data
        self.price = 0      # Item price in silver
        self.unpaid = False # Whether item is paid for
        
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
        """Return the EquipmentSlot this item belongs to"""
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
        elif self.item_type == ItemType.RANGED_WEAPON:
            return EquipmentSlot.RIGHT_HAND  # Ranged weapons typically go in the right hand
        elif self.item_type == ItemType.AMMO:
            return EquipmentSlot.LEFT_HAND  # Ammo/Quiver goes in the left hand
        else:
            return None  # Consumables, keys, misc items don't have a slot
        
    def __repr__(self):
        """String representation of Item"""
        return f"Item({self.item_type}, equippable={self.equippable})"

def heal_player(target, message_log=None, amount=10):
    """Healing item function"""
    # Use fixed healing amount instead of random
    healing = amount
    
    # Check if already at full health
    if target.fighter.hp == target.fighter.max_hp:
        if message_log:
            message_log.add_message("You're already at full health.")
        return False
        
    # Apply healing
    target.fighter.hp = min(target.fighter.hp + healing, target.fighter.max_hp)
    
    if message_log:
        message_log.add_message(f"You heal for {healing} hit points.")
    
    return True
