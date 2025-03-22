import random
from ...config import EntityType, LIGHT_BLUE, YELLOW

class Fighter:
    def __init__(self, hp=8, ac=11, damage_dice=(1, 3)):
        self.max_hp = hp
        self.hp = hp
        self.ac = ac  # Armor Class
        self.damage_dice = damage_dice  # Tuple of (number of dice, dice sides)
        self.owner = None
        # Character stats (3d6 for each)
        self.str = self.roll_stat()
        self.int = self.roll_stat()
        self.wis = self.roll_stat()
        self.dex = self.roll_stat()
        self.con = self.roll_stat()
        self.cha = self.roll_stat()
        # Experience and level
        self.xp = 0
        self.level = 1
        self.attack_bonus = 1  # Starting attack bonus at level 1
        
        # Level up table (level, xp_required, hit_dice, attack_bonus)
        self.level_table = [
            (1, 0, (1, 8), 1),
            (2, 200, (1, 8), 2),
            (3, 500, (1, 8), 2),
            (4, 1000, (1, 8), 3),
            (5, 2000, (1, 8), 4),
            (6, 3500, (1, 8), 4),
            (7, 5000, (1, 8), 5),
            (8, 7000, (1, 8), 6),
            (9, 10000, (1, 8), 6),
            (10, 14000, 2, 6),
            (11, 18000, 2, 7),
            (12, 23000, 2, 7),
            (13, 30000, 2, 8),
            (14, 40000, 2, 8),
            (15, 52000, 2, 8),
            (16, 65000, 2, 9),
            (17, 80000, 2, 9),
            (18, 100000, 2, 10),
            (19, 125000, 2, 10),
            (20, 150000, 2, 10)
        ]
    
    def roll_stat(self):
        """Roll 3d6 for a character stat"""
        return sum(random.randint(1, 6) for _ in range(3))
    
    def roll_damage(self):
        """Roll damage based on current weapon"""
        num_dice, dice_sides = self.damage_dice
        return sum(random.randint(1, dice_sides) for _ in range(num_dice))
    
    def take_damage(self, amount):
        self.hp -= amount
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
    
    def attack(self, target, message_log=None):
        # Roll to hit (1d20 + attack bonus for player)
        attack_roll = random.randint(1, 20)
        if self.owner.entity_type == EntityType.PLAYER:
            attack_roll += self.attack_bonus
        
        # Check if the attack hits (roll >= target's AC)
        if attack_roll >= target.fighter.ac:
            damage = self.roll_damage()
            if damage > 0:
                # Store original name before potential death changes it
                original_target_name = target.name
                
                # Deal damage and check result
                result = target.fighter.take_damage(damage)
                
                # Handle death and XP
                if result and 'dead:' in result:
                    # Extract the original name
                    killed_entity_name = result.split(':', 1)[1]
                    
                    # Award XP if player killed something
                    if self.owner.entity_type == EntityType.PLAYER and message_log:
                        xp_amount = 0
                        
                        # Find the monster in our list by name
                        from ...data.monsters import MONSTERS
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
                            for level, xp_threshold, hit_dice, attack_bonus in self.level_table:
                                if level > self.level and self.xp >= xp_threshold:
                                    self.level_up(level, hit_dice, attack_bonus, message_log)
                                    break
                    
                    # Use original name in message to avoid saying "remains of..."
                    return f'{self.owner.name} attacks {original_target_name} for {damage} hit points and kills it!'
                elif result == 'dead':
                    return f'{self.owner.name} attacks {original_target_name} for {damage} hit points and kills it!'
                else:
                    return f'{self.owner.name} attacks {target.name} for {damage} hit points!'
            else:
                return f'{self.owner.name} attacks {target.name} but does no damage!'
        else:
            return f'{self.owner.name} attacks {target.name} but misses!'
    
    def gain_xp(self, amount, message_log=None):
        """Gain experience points and check for level up"""
        if self.level >= 20:  # Already at max level
            return
            
        self.xp += amount
        if message_log:
            message_log.add_message(f"You gain {amount} experience points.", LIGHT_BLUE)
        
        # Check for level up
        for level, xp_threshold, hit_dice, attack_bonus in self.level_table:
            if level > self.level and self.xp >= xp_threshold:
                self.level_up(level, hit_dice, attack_bonus, message_log)
                break
    
    def level_up(self, new_level, hit_dice, attack_bonus, message_log=None):
        """Level up the character"""
        old_level = self.level
        self.level = new_level
        
        # Increase max hit points
        if isinstance(hit_dice, tuple):
            # Roll dice for HP increase
            num_dice, dice_sides = hit_dice
            hp_increase = sum(random.randint(1, dice_sides) for _ in range(num_dice))
        else:
            # Fixed HP increase
            hp_increase = hit_dice
            
        self.max_hp += hp_increase
        self.hp += hp_increase  # Also heal current HP
        
        # Update attack bonus
        self.attack_bonus = attack_bonus
        
        if message_log:
            message_log.add_message(f"You advance to level {new_level}!", YELLOW)
            message_log.add_message(f"Your maximum HP increases by {hp_increase}!", YELLOW)
            if attack_bonus > self.attack_bonus:
                message_log.add_message(f"Your attack bonus increases to +{attack_bonus}!", YELLOW)
    
    def get_next_level_xp(self):
        """Get XP needed for next level"""
        if self.level >= 20:
            return None  # Already at max level
            
        for level, xp_threshold, _, _ in self.level_table:
            if level > self.level:
                return xp_threshold
                
        return None  # No next level found
