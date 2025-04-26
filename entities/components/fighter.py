import random
from config import EntityType, LIGHT_BLUE, YELLOW

class Fighter:
    def __init__(self, hp=8, armor=2, damage_dice=(1, 3)):
        self.max_hp = hp
        self.hp = hp
        self.armor = armor  # Damage reduction (renamed from AC)
        self.dodge = 10  # Base dodge chance (chance to completely avoid an attack)
        self.damage_dice = damage_dice  # Tuple of (number of dice, dice sides)
        self.owner = None
        
        # Character stats (starting range 5-10)
        self.str = random.randint(5, 10)
        self.int = random.randint(5, 10)
        self.wis = random.randint(5, 10)
        self.dex = random.randint(5, 10)
        self.con = random.randint(5, 10)
        self.cha = random.randint(5, 10)
        
        # Attribute points to distribute (awarded on level up)
        self.attr_points = 0
        
        # Experience and level
        self.xp = 0
        self.level = 1
        self.attack_bonus = 1  # Starting attack bonus at level 1
        
        # Level up table (level, xp_required, hit_dice, attack_bonus, attribute_points)
        self.level_table = [
            (1, 0, (1, 8), 1, 0),
            (2, 200, (1, 8), 2, 2),
            (3, 500, (1, 8), 2, 2),
            (4, 1000, (1, 8), 3, 2),
            (5, 2000, (1, 8), 4, 3),
            (6, 3500, (1, 8), 4, 3),
            (7, 5000, (1, 8), 5, 3),
            (8, 7000, (1, 8), 6, 3),
            (9, 10000, (1, 8), 6, 4),
            (10, 14000, 2, 6, 4),
            (11, 18000, 2, 7, 4),
            (12, 23000, 2, 7, 4),
            (13, 30000, 2, 8, 5),
            (14, 40000, 2, 8, 5),
            (15, 52000, 2, 8, 5),
            (16, 65000, 2, 9, 5),
            (17, 80000, 2, 9, 5),
            (18, 100000, 2, 10, 6),
            (19, 125000, 2, 10, 6),
            (20, 150000, 2, 10, 6),
            (21, 180000, 2, 11, 6),  # Continue beyond level 20
            (22, 215000, 2, 11, 6),
            (23, 255000, 2, 12, 7),
            (24, 300000, 2, 12, 7),
            (25, 350000, 2, 13, 7)
        ]
    
    def get_dodge_chance(self):
        """Calculate character's dodge chance based on dexterity"""
        return self.dodge + max(0, (self.dex - 10) // 2)
    
    def get_damage_bonus(self):
        """Calculate melee damage bonus based on strength"""
        return max(0, (self.str - 10) // 5)
    
    def get_ranged_bonus(self):
        """Calculate ranged attack bonus based on dexterity"""
        return max(0, (self.dex - 10) // 5)
    
    def get_hp_bonus(self):
        """Calculate HP bonus based on constitution"""
        return max(0, self.con - 10)
    
    def roll_damage(self):
        """Roll damage based on current weapon and add strength bonus"""
        num_dice, dice_sides = self.damage_dice
        base_damage = sum(random.randint(1, dice_sides) for _ in range(num_dice))
        
        # Add strength bonus for melee weapons
        # Check if owner has a ranged weapon equipped
        if self.owner and self.owner.inventory:
            ranged_weapon = self.owner.inventory.get_equipped_ranged_weapon()
            if not ranged_weapon:  # If no ranged weapon, assume melee
                return base_damage + self.get_damage_bonus()
        
        return base_damage
    
    def take_damage(self, amount):
        # Apply armor damage reduction
        reduced_damage = max(1, amount - self.armor)  # Always take at least 1 damage
        self.hp -= reduced_damage
        
        if self.hp <= 0:
            # If the owner is the player, game over
            if self.owner.entity_type == EntityType.PLAYER:
                return 'dead'
            else:
                # Entity died - handle XP award if killed by player
                self.owner.char = '%'  # Dead enemy becomes a corpse
                self.owner.blocks = False
                self.owner.fighter = None
                self.owner.ai = None
                
                # Store original name for XP checking before changing it
                original_name = self.owner.name
                self.owner.name = f'remains of {original_name}'
                
                # Return the original name to check for XP in the calling method
                return f'dead:{original_name}'
        
        return f'damaged:{reduced_damage}'
    
    def attack(self, target, message_log=None):
        # Determine if attack hits based on dodge chance
        dodge_chance = target.fighter.get_dodge_chance()
        hit_roll = random.randint(1, 100)
        
        # If roll is higher than dodge chance, the attack hits
        if hit_roll > dodge_chance:
            damage = self.roll_damage()
            if damage > 0:
                # Store original name before potential death changes it
                original_target_name = target.name
                
                # Deal damage and check result
                result = target.fighter.take_damage(damage)
                
                # Check if it's a damage result with reduced damage info
                if result and result.startswith('damaged:'):
                    # Extract the reduced damage
                    reduced_damage = int(result.split(':', 1)[1])
                    damage_reduction = damage - reduced_damage
                    
                    # Show both original damage and reduced damage
                    if damage_reduction > 0:
                        attack_msg = f'{self.owner.name} attacks {target.name} for {damage} damage ({reduced_damage} after armor)!'
                    else:
                        attack_msg = f'{self.owner.name} attacks {target.name} for {reduced_damage} damage!'
                
                # Handle death and XP
                elif result and 'dead:' in result:
                    # Extract the original name
                    killed_entity_name = result.split(':', 1)[1]
                    
                    # Award XP if player killed something
                    if self.owner.entity_type == EntityType.PLAYER and message_log:
                        xp_amount = 0
                        
                        # Find the monster in our list by name
                        from data.monsters import MONSTERS
                        for monster_key, monster_data in MONSTERS.items():
                            if monster_data.name.lower() in killed_entity_name.lower():
                                xp_amount = monster_data.xp
                                break
                        
                        # Fallback for monsters not in the list (should be rare)
                        if xp_amount == 0:
                            if 'Orc' in killed_entity_name:
                                xp_amount = 50
                            elif 'Troll' in killed_entity_name:
                                xp_amount = 100
                        
                        if xp_amount > 0:
                            message_log.add_message(f"You killed a {killed_entity_name} and gained {xp_amount} XP!", LIGHT_BLUE)
                            
                            # Add XP directly and check for level up
                            old_level = self.level
                            self.xp += xp_amount
                            
                            # Check for level up
                            for level, xp_threshold, hit_dice, attack_bonus, attr_points in self.level_table:
                                if level > self.level and self.xp >= xp_threshold:
                                    self.level_up(level, hit_dice, attack_bonus, attr_points, message_log)
                                    break
                    
                    # Use original name in message to avoid saying "remains of..."
                    return f'{self.owner.name} attacks {original_target_name} for {damage} damage and kills it!'
                elif result == 'dead':
                    return f'{self.owner.name} attacks {original_target_name} for {damage} damage and kills it!'
                else:
                    return attack_msg
            else:
                return f'{self.owner.name} attacks {target.name} but does no damage!'
        else:
            return f'{self.owner.name} attacks {target.name} but misses! ({target.name} dodged)'
    
    def gain_xp(self, amount, message_log=None):
        """Gain experience points and check for level up"""
        # No level cap - continue past level 20
        self.xp += amount
        if message_log:
            message_log.add_message(f"You gain {amount} experience points.", LIGHT_BLUE)
        
        # Check for level up
        for level, xp_threshold, hit_dice, attack_bonus, attr_points in self.level_table:
            if level > self.level and self.xp >= xp_threshold:
                self.level_up(level, hit_dice, attack_bonus, attr_points, message_log)
                break
    
    def level_up(self, new_level, hit_dice, attack_bonus, attr_points, message_log=None):
        """Level up the character"""
        old_level = self.level
        self.level = new_level
        
        # Increase max hit points
        if isinstance(hit_dice, tuple):
            # Roll dice for HP increase
            num_dice, dice_sides = hit_dice
            hp_increase = sum(random.randint(1, dice_sides) for _ in range(num_dice))
            
            # Add constitution bonus
            hp_increase += self.get_hp_bonus()
        else:
            # Fixed HP increase plus constitution bonus
            hp_increase = hit_dice + self.get_hp_bonus()
            
        self.max_hp += hp_increase
        self.hp += hp_increase  # Also heal current HP
        
        # Update attack bonus
        self.attack_bonus = attack_bonus
        
        # Add attribute points to distribute
        self.attr_points += attr_points
        
        if message_log:
            message_log.add_message(f"You advance to level {new_level}!", YELLOW)
            message_log.add_message(f"Your maximum HP increases by {hp_increase}!", YELLOW)
            if attr_points > 0:
                message_log.add_message(f"You gain {attr_points} attribute points to distribute!", YELLOW)
    
    def increase_attribute(self, attribute, amount=1):
        """Increase a specific attribute by the given amount"""
        if self.attr_points >= amount:
            if attribute == 'str':
                self.str += amount
            elif attribute == 'int':
                self.int += amount
            elif attribute == 'wis':
                self.wis += amount
            elif attribute == 'dex':
                self.dex += amount
                # Update dodge when dexterity changes
                self.dodge = self.get_dodge_chance()
            elif attribute == 'con':
                self.con += amount
                # Update max HP when constitution changes
                hp_increase = amount
                self.max_hp += hp_increase
                self.hp += hp_increase
            elif attribute == 'cha':
                self.cha += amount
            
            self.attr_points -= amount
            return True
        return False
    
    def get_next_level_xp(self):
        """Get XP needed for next level"""
        # Check if we've exceeded our defined level table
        if self.level >= len(self.level_table):
            last_level = self.level_table[-1]
            # Generate a reasonable next XP threshold (25% increase from previous)
            return int(last_level[1] * 1.25)
            
        for level, xp_threshold, _, _, _ in self.level_table:
            if level > self.level:
                return xp_threshold
                
        # If we get here, create a fallback calculation
        last_known_level = self.level_table[-1]
        return int(last_known_level[1] * 1.25)
