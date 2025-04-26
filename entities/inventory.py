from config import EquipmentSlot, ItemType, RED, YELLOW, LIGHT_BLUE

class Inventory:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.items = []  # Regular inventory items
        self.equipment = {
            EquipmentSlot.RIGHT_HAND: None,
            EquipmentSlot.LEFT_HAND: None,
            EquipmentSlot.HEAD: None,
            EquipmentSlot.TORSO: None,
            EquipmentSlot.LEGS: None,
            EquipmentSlot.HANDS: None,
            EquipmentSlot.FEET: None
        }
        self.owner = None
        
    def add_item(self, item, message_log):
        if len(self.items) >= self.capacity:
            message_log.add_message("Your inventory is full!", RED)
            return False
            
        self.items.append(item)
        
        # Different message for unpaid items
        if item.item and item.item.unpaid:
            message_log.add_message(f"You pick up the {item.name} (unpaid)!", LIGHT_BLUE)
        else:
            message_log.add_message(f"You pick up the {item.name}!", LIGHT_BLUE)
        return True
        
    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def get_equipped_item(self, slot):
        return self.equipment[slot]
    
    def equip_item(self, item, slot, message_log, entities=None):
        # Check if the item is a two-handed weapon
        is_two_handed = (item.item.weapon_data and item.item.weapon_data.is_two_handed)
        
        # Check if we're trying to equip to a hand slot
        is_hand_slot = (slot == EquipmentSlot.RIGHT_HAND or slot == EquipmentSlot.LEFT_HAND)
        
        # Get current equipment in both hands
        right_hand_item = self.equipment[EquipmentSlot.RIGHT_HAND]
        left_hand_item = self.equipment[EquipmentSlot.LEFT_HAND]
        
        # Case 1: Equipping a two-handed weapon
        if is_two_handed:
            # Unequip both hands if they're occupied
            if right_hand_item:
                # Special handling for two-handed weapon already in right hand
                if right_hand_item == left_hand_item and right_hand_item.item.weapon_data and right_hand_item.item.weapon_data.is_two_handed:
                    success = self.unequip_item(EquipmentSlot.RIGHT_HAND, message_log, entities)
                    if not success:
                        message_log.add_message(f"Cannot equip - inventory full!", RED)
                        return False
                else:
                    success = self.unequip_item(EquipmentSlot.RIGHT_HAND, message_log, entities)
                    if not success:
                        message_log.add_message(f"Cannot equip - right hand item can't be unequipped!", RED)
                        return False
            
            # Only try to unequip left hand if it's not the same as right hand (would be already unequipped)
            if left_hand_item and left_hand_item != right_hand_item:
                success = self.unequip_item(EquipmentSlot.LEFT_HAND, message_log, entities)
                if not success:
                    message_log.add_message(f"Cannot equip - left hand item can't be unequipped!", RED)
                    # Re-equip right hand if needed
                    if right_hand_item and right_hand_item not in self.items:
                        self.items.remove(right_hand_item)
                        self.equipment[EquipmentSlot.RIGHT_HAND] = right_hand_item
                        self._update_fighter_stats(right_hand_item, True)
                    return False
            
            # Remove the item from inventory
            self.remove_item(item)
            
            # Equip the two-handed weapon to both slots
            self.equipment[EquipmentSlot.RIGHT_HAND] = item
            self.equipment[EquipmentSlot.LEFT_HAND] = item  # Same reference in both slots
            
            # Apply bonuses
            self._update_fighter_stats(item, True)
            
            message_log.add_message(f"You equip the {item.name} with both hands.", LIGHT_BLUE)
            return True
            
        # Case 2: Equipping a one-handed item to hand slot
        elif is_hand_slot:
            # Check if a two-handed weapon is equipped (will be in both slots)
            two_handed_equipped = (right_hand_item == left_hand_item and 
                                 right_hand_item is not None and 
                                 right_hand_item.item.weapon_data and 
                                 right_hand_item.item.weapon_data.is_two_handed)
            
            if two_handed_equipped:
                # Need to unequip the two-handed weapon
                success = self.unequip_item(EquipmentSlot.RIGHT_HAND, message_log, entities)
                if not success:
                    message_log.add_message(f"Cannot equip - two-handed weapon can't be unequipped!", RED)
                    return False
            
            # Now handle the specific slot normally
            if self.equipment[slot]:
                current_item = self.equipment[slot]
                if len(self.items) < self.capacity:
                    self.items.append(current_item)
                    self._update_fighter_stats(current_item, False)
                else:
                    # Drop the item if inventory is full
                    current_item.x = self.owner.x
                    current_item.y = self.owner.y
                    if entities is not None:
                        entities.append(current_item)
                    message_log.add_message(f"You drop the {current_item.name} since your inventory is full.", YELLOW)
            
            # Remove the item from inventory and equip it
            self.remove_item(item)
            self.equipment[slot] = item
            self._update_fighter_stats(item, True)
            
            message_log.add_message(f"You equip the {item.name}.", LIGHT_BLUE)
            return True
            
        # Case 3: Non-hand equipment (helmet, armor, etc.)
        else:
            # Standard equipment logic
            if self.equipment[slot]:
                current_item = self.equipment[slot]
                if len(self.items) < self.capacity:
                    self.items.append(current_item)
                    self._update_fighter_stats(current_item, False)
                else:
                    # Drop the item if inventory is full
                    current_item.x = self.owner.x
                    current_item.y = self.owner.y
                    if entities is not None:
                        entities.append(current_item)
                    message_log.add_message(f"You drop the {current_item.name} since your inventory is full.", YELLOW)
            
            # Remove the item from inventory and equip it
            self.remove_item(item)
            self.equipment[slot] = item
            self._update_fighter_stats(item, True)
            
            message_log.add_message(f"You equip the {item.name}.", LIGHT_BLUE)
            return True
    
    def unequip_item(self, slot, message_log, entities):
        item = self.equipment[slot]
        if not item:
            return False
        
        # Check if it's a two-handed weapon
        is_two_handed = (item.item.weapon_data and item.item.weapon_data.is_two_handed)
        
        # Remove bonuses from item
        self._update_fighter_stats(item, False)
        
        # Try to add back to inventory
        if len(self.items) < self.capacity:
            self.items.append(item)
            
            # For two-handed weapons, clear both slots
            if is_two_handed:
                # Only clear both slots if they're the same item (two-handed weapon)
                if self.equipment[EquipmentSlot.RIGHT_HAND] == self.equipment[EquipmentSlot.LEFT_HAND]:
                    self.equipment[EquipmentSlot.RIGHT_HAND] = None
                    self.equipment[EquipmentSlot.LEFT_HAND] = None
            else:
                self.equipment[slot] = None
                
            message_log.add_message(f"You unequip the {item.name}.", LIGHT_BLUE)
            return True
        else:
            # Drop the item if inventory is full
            # First check if something already exists at this spot
            for entity in entities:
                if entity.x == self.owner.x and entity.y == self.owner.y and entity.entity_type == EntityType.ITEM:
                    message_log.add_message(f"Cannot unequip - inventory full and an item is already on the ground.", RED)
                    # Re-apply bonuses since we couldn't unequip
                    self._update_fighter_stats(item, True)
                    return False
            
            item.x = self.owner.x
            item.y = self.owner.y
            
            # For two-handed weapons, clear both slots
            if is_two_handed:
                # Only clear both slots if they're the same item (two-handed weapon)
                if self.equipment[EquipmentSlot.RIGHT_HAND] == self.equipment[EquipmentSlot.LEFT_HAND]:
                    self.equipment[EquipmentSlot.RIGHT_HAND] = None
                    self.equipment[EquipmentSlot.LEFT_HAND] = None
            else:
                self.equipment[slot] = None
                
            entities.append(item)
            message_log.add_message(f"You unequip and drop the {item.name} since your inventory is full.", YELLOW)
            return True
    
    def _update_fighter_stats(self, item, is_equipping):
        """Update fighter stats based on equipped/unequipped item"""
        if not item or not item.item:
            return
            
        # Handle weapon damage dice
        if item.item.damage_dice and item.item.get_slot() == EquipmentSlot.RIGHT_HAND:
            if is_equipping:
                self.owner.fighter.damage_dice = item.item.damage_dice
            else:
                # Reset to default damage dice if unequipping
                self.owner.fighter.damage_dice = (1, 3)
        
        # Handle armor and dodge bonuses for all equipment
        if item.item.armor_bonus != 0:
            if is_equipping:
                self.owner.fighter.armor += item.item.armor_bonus
            else:
                self.owner.fighter.armor -= item.item.armor_bonus
        
        if item.item.dodge_bonus != 0:
            if is_equipping:
                self.owner.fighter.dodge += item.item.dodge_bonus
            else:
                self.owner.fighter.dodge -= item.item.dodge_bonus
            
        # Recalculate dodge chance after equipment changes
        if hasattr(self.owner.fighter, 'get_dodge_chance'):
            self.owner.fighter.dodge = self.owner.fighter.get_dodge_chance()
    
    def find_item_by_type(self, item_type):
        """Find the first item of a specific type in inventory"""
        for item in self.items:
            if item.item and item.item.item_type == item_type:
                return item
        return None
        
    def get_ammo(self):
        """Get the equipped ammo"""
        ammo_item = self.get_equipped_item(EquipmentSlot.LEFT_HAND)
        if ammo_item and ammo_item.item and ammo_item.item.item_type == ItemType.AMMO:
            return ammo_item
        return None
        
    def get_equipped_ranged_weapon(self):
        """Get the equipped ranged weapon"""
        weapon = self.get_equipped_item(EquipmentSlot.RIGHT_HAND)
        if weapon and weapon.item and weapon.item.item_type == ItemType.RANGED_WEAPON:
            return weapon
        return None
        
    def has_ammo_for_weapon(self):
        """Check if player has ammo for their equipped ranged weapon"""
        weapon = self.get_equipped_ranged_weapon()
        ammo = self.get_ammo()
        
        if not weapon or not ammo:
            return False
            
        # Check if ammo type matches weapon's required ammo type
        if weapon.item.weapon_data.ammo_type == ammo.item.ammo_data.ammo_type:
            # Check if there are arrows left
            if ammo.item.ammo_data.current > 0:
                return True
                
        return False
    
    def has_space(self):
        """Check if the inventory has available space"""
        return len(self.items) < self.capacity
        
    def use_ammo(self):
        """Use one unit of ammo and return True if successful"""
        ammo = self.get_ammo()
        if ammo and ammo.item and ammo.item.ammo_data.current > 0:
            ammo.item.ammo_data.current -= 1
            
            # If quiver is empty, remove it
            if ammo.item.ammo_data.current <= 0:
                # Check if the empty quiver is equipped and unequip it if needed
                for slot, equipped_item in self.equipment.items():
                    if equipped_item == ammo:
                        self.equipment[slot] = None
                        break
                        
                try:
                    self.items.remove(ammo)
                except ValueError:
                    # If the ammo is not in the list for some reason, just continue
                    pass
            return True
        return False

    def has_unpaid_items(self):
        """Check if the player has any unpaid items in inventory"""
        for item in self.items:
            if item.item and item.item.unpaid:
                return True
        
        # Also check equipment slots
        for slot in self.equipment:
            item = self.equipment[slot]
            if item and item.item and item.item.unpaid:
                return True
            
        return False
    
    def get_unpaid_items(self):
        """Return a list of all unpaid items"""
        unpaid_items = []
        
        # Check inventory
        for item in self.items:
            if item.item and item.item.unpaid:
                unpaid_items.append(item)
        
        # Check equipment
        for slot in self.equipment:
            item = self.equipment[slot]
            if item and item.item and item.item.unpaid:
                unpaid_items.append(item)
            
        return unpaid_items
    
    def calculate_total_price(self):
        """Calculate the total price of all unpaid items"""
        total = 0
        for item in self.get_unpaid_items():
            total += item.item.price
        return total
    
    def pay_for_items(self, message_log):
        """Attempt to pay for all unpaid items"""
        if not self.has_unpaid_items():
            message_log.add_message("You don't have any unpaid items.", YELLOW)
            return False
        
        total_price = self.calculate_total_price()
        
        if self.owner.silver_pieces < total_price:
            message_log.add_message(f"You need {total_price} silver, but only have {self.owner.silver_pieces}.", RED)
            return False
        
        # Pay for the items
        self.owner.silver_pieces -= total_price
        
        # Mark items as paid
        for item in self.get_unpaid_items():
            item.item.unpaid = False
        
        message_log.add_message(f"You pay {total_price} silver for your purchases.", LIGHT_BLUE)
        return True
