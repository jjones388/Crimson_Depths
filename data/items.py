import random
from config import EntityType, ItemType, WHITE, YELLOW, LIGHT_BLUE
from entities.entity import Entity
from entities.components.item import Item, heal_player
from data.monsters import MONSTERS
from entities.components.ai import BasicMonster
from entities.components.fighter import Fighter

# Item prices
ITEM_PRICES = {
    # Weapons
    "dagger": 5,
    "shortsword": 10,
    "longsword": 15,
    "mace": 8,
    "battleaxe": 20,
    "warhammer": 25,
    "shortbow": 15,
    "longbow": 30,
    
    # Armor
    "leather_armor": 10,
    "chainmail": 25,
    "plate_armor": 50,
    "helmet": 15,
    "boots": 12,
    "gloves": 10,
    "shield": 8,
    
    # Consumables
    "healing_potion": 20,
    "arrows": 5
}

# Define weapon data structure
class WeaponData:
    def __init__(self, name, weapon_type, damage_type, size, damage_dice, ranged=False, ammo_type=None, range=None):
        self.name = name
        self.weapon_type = weapon_type
        self.damage_type = damage_type
        self.size = size  # 'S', 'M', or 'L'
        self.damage_dice = damage_dice  # tuple of (count, sides)
        self.ranged = ranged  # True if it's a ranged weapon
        self.ammo_type = ammo_type  # Type of ammunition this weapon uses
        self.range = range  # Maximum firing range in tiles
        
    @property
    def is_two_handed(self):
        return self.size == 'L'

# Define all weapons
WEAPONS = {
    'hand_axe': WeaponData('Hand Axe', 'Axe', 'Edge', 'S', (1, 6)),
    'battle_axe': WeaponData('Battle Axe', 'Axe', 'Edge', 'M', (1, 8)),
    'great_axe': WeaponData('Great Axe', 'Axe', 'Edge', 'L', (1, 10)),
    'dagger': WeaponData('Dagger', 'Dagger', 'Edge', 'S', (1, 4)),
    'short_sword': WeaponData('Short Sword', 'Sword', 'Edge', 'S', (1, 6)),
    'long_sword': WeaponData('Long Sword', 'Sword', 'Edge', 'M', (1, 8)),
    'great_sword': WeaponData('Great Sword', 'Sword', 'Edge', 'L', (1, 10)),
    'warhammer': WeaponData('Warhammer', 'Mace', 'Blunt', 'S', (1, 6)),
    'mace': WeaponData('Mace', 'Mace', 'Blunt', 'M', (1, 8)),
    'maul': WeaponData('Maul', 'Mace', 'Blunt', 'L', (1, 10)),
    'club': WeaponData('Club', 'Staff', 'Blunt', 'S', (1, 4)),
    'walking_staff': WeaponData('Walking Staff', 'Staff', 'Blunt', 'M', (1, 4)),
    'quarter_staff': WeaponData('Quarter Staff', 'Staff', 'Blunt', 'L', (1, 6)),
    'spear': WeaponData('Spear', 'Spear', 'Piercing', 'M', (1, 6)),
    'shortbow': WeaponData('Shortbow', 'Bow', 'Piercing', 'M', (1, 6), ranged=True, ammo_type='Arrow', range=10),
}

# Define ammo types
class AmmoData:
    def __init__(self, name, ammo_type, capacity):
        self.name = name
        self.ammo_type = ammo_type
        self.capacity = capacity  # How many shots this ammo can provide
        self.current = capacity   # Current ammo count

# Define available ammo
AMMO = {
    'arrows': AmmoData('Quiver of Arrows', 'Arrow', 20),
}

def place_entities(room, entities, max_enemies_per_room, max_items_per_room, dungeon_level=1):
    # Random number of enemies
    number_of_enemies = random.randint(0, max_enemies_per_room)
    
    # Random number of items
    number_of_items = random.randint(0, max_items_per_room)
    
    # 30% chance to place silver in a room
    has_silver = random.random() < 0.3
    
    # Get eligible monsters for this dungeon level
    eligible_monsters = [
        monster for monster in MONSTERS.values() 
        if monster.min_level <= dungeon_level <= monster.max_level
    ]
    
    # Place enemies
    for i in range(number_of_enemies):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        
        # Check if position is empty
        if not any(entity.x == x and entity.y == y for entity in entities):
            if eligible_monsters:
                # Choose a random monster from eligible ones
                monster_data = random.choice(eligible_monsters)
                
                # Calculate hit points
                if isinstance(monster_data.hit_dice, tuple):
                    dice_count, dice_sides = monster_data.hit_dice
                    hp = sum(random.randint(1, dice_sides) for _ in range(dice_count))
                elif monster_data.hit_dice == 0.5:  # 1/2 HD
                    hp = random.randint(1, 4)
                elif monster_data.hit_dice == 0.25:  # 1/4 HD
                    hp = random.randint(1, 3)
                else:
                    hp = random.randint(1, 8)  # Default 1 HD
                
                # Create fighter component
                fighter_component = Fighter(
                    hp=hp,
                    armor=monster_data.armor,
                    damage_dice=monster_data.damage_dice
                )
                
                # Copy dodge from monster_data to fighter_component
                fighter_component.dodge = monster_data.dodge
                
                ai_component = BasicMonster()
                
                # Create entity
                enemy = Entity(
                    x, y, 
                    monster_data.char, 
                    WHITE,  # All monsters white for now as requested
                    EntityType.ENEMY, 
                    monster_data.name, 
                    blocks=True, 
                    fighter=fighter_component, 
                    ai=ai_component
                )
                
                entities.append(enemy)
            else:
                # Fallback to default monsters if no eligible ones
                if random.random() < 0.8:
                    # 80% chance for an orc - 1d4 HP, 1 armor, 1d4 damage
                    fighter_component = Fighter(
                        hp=random.randint(1, 4),
                        armor=1,  # Low armor
                        damage_dice=(1, 4)
                    )
                    # Set dodge chance
                    fighter_component.dodge = 12  # Moderate dodge
                    
                    ai_component = BasicMonster()
                    
                    enemy = Entity(x, y, 'o', WHITE, EntityType.ENEMY, 'Orc', blocks=True,
                                   fighter=fighter_component, ai=ai_component)
                else:
                    # 20% chance for a troll - 1d8, 3 armor, 1d6 damage
                    fighter_component = Fighter(
                        hp=random.randint(1, 8) + 4,
                        armor=3,  # Better armor
                        damage_dice=(1, 6)
                    )
                    # Set dodge chance
                    fighter_component.dodge = 7  # Low dodge (slower)

                ai_component = BasicMonster()
                
                enemy = Entity(x, y, 'T', WHITE, EntityType.ENEMY, 'Troll', blocks=True, 
                              fighter=fighter_component, ai=ai_component)
                
                entities.append(enemy)
    
    # Place items
    for i in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        
        # Check if position is empty
        if not any(entity.x == x and entity.y == y for entity in entities):
            item_choice = random.random()
            
            if item_choice < 0.35:  # 35% chance for healing potion
                item_component = Item(use_function=heal_player, item_type=ItemType.CONSUMABLE)
                item = Entity(x, y, '!', YELLOW, EntityType.ITEM, 'Healing Potion', blocks=False, item=item_component)
            elif item_choice < 0.65:  # 30% chance for a weapon
                # Choose a random weapon
                weapon_key = random.choice(list(WEAPONS.keys()))
                weapon = WEAPONS[weapon_key]
                
                # Determine if it's a ranged weapon
                if weapon.ranged:
                    item_component = Item(
                        item_type=ItemType.RANGED_WEAPON, 
                        equippable=True,
                        damage_dice=weapon.damage_dice,
                        weapon_data=weapon
                    )
                    
                    # Use '}' for bows (bow shape in ASCII/CP437)
                    char = '}'
                else:
                    item_component = Item(
                        item_type=ItemType.WEAPON, 
                        equippable=True,
                        damage_dice=weapon.damage_dice,
                        weapon_data=weapon
                    )
                    
                    # Use '/' for all melee weapons (ASCII value 47 in CP437)
                    char = '/'
                
                item = Entity(x, y, char, WHITE, EntityType.ITEM, weapon.name, blocks=False, item=item_component)
            elif item_choice < 0.75:  # 10% chance for a shield
                item_component = Item(
                    item_type=ItemType.SHIELD, 
                    equippable=True,
                    armor_bonus=1,  # Damage reduction
                    dodge_bonus=0   # No dodge bonus
                )
                item = Entity(x, y, '[', WHITE, EntityType.ITEM, 'Shield', blocks=False, item=item_component)
            elif item_choice < 0.80:  # 5% chance for ammo
                # Choose a random ammo
                ammo_key = random.choice(list(AMMO.keys()))
                ammo = AMMO[ammo_key]
                
                # Create a new AmmoData instance to ensure it's a fresh supply
                ammo_instance = AmmoData(ammo.name, ammo.ammo_type, ammo.capacity)
                
                item_component = Item(
                    item_type=ItemType.AMMO,
                    equippable=True,
                    ammo_data=ammo_instance
                )
                
                # Use '(' for quivers (quiver shape in ASCII/CP437)
                item = Entity(x, y, '(', WHITE, EntityType.ITEM, ammo.name, blocks=False, item=item_component)
            elif item_choice < 0.85:  # 5% chance for a helmet
                item_component = Item(
                    item_type=ItemType.HELMET, 
                    equippable=True,
                    armor_bonus=1,  # Damage reduction
                    dodge_bonus=0   # No dodge bonus
                )
                item = Entity(x, y, '^', LIGHT_BLUE, EntityType.ITEM, 'Helmet', blocks=False, item=item_component)
            elif item_choice < 0.95:  # 10% chance for armor
                item_component = Item(
                    item_type=ItemType.ARMOR, 
                    equippable=True,
                    armor_bonus=3,  # Good damage reduction
                    dodge_bonus=-5  # Reduces dodge (heavy armor)
                )
                item = Entity(x, y, '#', LIGHT_BLUE, EntityType.ITEM, 'Chainmail', blocks=False, item=item_component)
            else:  # 5% chance for boots
                item_component = Item(
                    item_type=ItemType.BOOTS, 
                    equippable=True,
                    armor_bonus=0,  # No damage reduction
                    dodge_bonus=5   # Improves dodge chance
                )
                item = Entity(x, y, '>', LIGHT_BLUE, EntityType.ITEM, 'Boots', blocks=False, item=item_component)
            
            entities.append(item)
    
    # Place silver if this room has it
    if has_silver:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        
        # Check if position is empty
        if not any(entity.x == x and entity.y == y for entity in entities):
            # Random amount between 1-10 silver pieces
            amount = random.randint(1, 10)
            silver = Entity(x, y, '$', YELLOW, EntityType.ITEM, 'Silver', blocks=False, silver_pieces=amount)
            entities.append(silver)

def create_item(item_name, x, y):
    """Create an item entity by its name"""
    if item_name in WEAPONS:
        weapon = WEAPONS[item_name]
        
        # Determine if it's a ranged weapon
        if weapon.ranged:
            item_component = Item(
                item_type=ItemType.RANGED_WEAPON, 
                equippable=True,
                damage_dice=weapon.damage_dice,
                weapon_data=weapon
            )
            
            # Use '}' for bows (bow shape in ASCII/CP437)
            char = '}'
        else:
            item_component = Item(
                item_type=ItemType.WEAPON, 
                equippable=True,
                damage_dice=weapon.damage_dice,
                weapon_data=weapon
            )
            
            # Use '/' for all melee weapons (ASCII value 47 in CP437)
            char = '/'
        
        return Entity(x, y, char, WHITE, EntityType.ITEM, weapon.name, blocks=False, item=item_component)
    
    elif item_name in AMMO:
        ammo = AMMO[item_name]
        
        # Create a new AmmoData instance to ensure it's a fresh supply
        ammo_instance = AmmoData(ammo.name, ammo.ammo_type, ammo.capacity)
        
        item_component = Item(
            item_type=ItemType.AMMO,
            equippable=True,
            ammo_data=ammo_instance
        )
        
        # Use '(' for quivers (quiver shape in ASCII/CP437)
        return Entity(x, y, '(', WHITE, EntityType.ITEM, ammo.name, blocks=False, item=item_component)
    
    # If item is a healing potion
    elif item_name == 'healing_potion':
        item_component = Item(use_function=heal_player, item_type=ItemType.CONSUMABLE)
        return Entity(x, y, '!', YELLOW, EntityType.ITEM, 'Healing Potion', blocks=False, item=item_component)
    
    # Armor items
    elif item_name == 'leather_armor':
        item_component = Item(
            item_type=ItemType.ARMOR, 
            equippable=True,
            armor_bonus=2,  # Light damage reduction
            dodge_bonus=0   # No dodge penalty
        )
        return Entity(x, y, '#', LIGHT_BLUE, EntityType.ITEM, 'Leather Armor', blocks=False, item=item_component)
    
    elif item_name == 'chainmail':
        item_component = Item(
            item_type=ItemType.ARMOR, 
            equippable=True,
            armor_bonus=3,  # Medium damage reduction
            dodge_bonus=-5  # Reduces dodge
        )
        return Entity(x, y, '#', LIGHT_BLUE, EntityType.ITEM, 'Chainmail', blocks=False, item=item_component)
    
    elif item_name == 'plate_armor':
        item_component = Item(
            item_type=ItemType.ARMOR, 
            equippable=True,
            armor_bonus=5,  # Best damage reduction
            dodge_bonus=-10 # Significantly reduces dodge
        )
        return Entity(x, y, '#', LIGHT_BLUE, EntityType.ITEM, 'Plate Armor', blocks=False, item=item_component)
    
    # Other equipment
    elif item_name == 'helmet':
        item_component = Item(
            item_type=ItemType.HELMET, 
            equippable=True,
            armor_bonus=1,  # Small damage reduction
            dodge_bonus=0   # No dodge effect
        )
        return Entity(x, y, '^', LIGHT_BLUE, EntityType.ITEM, 'Helmet', blocks=False, item=item_component)
    
    elif item_name == 'boots':
        item_component = Item(
            item_type=ItemType.BOOTS, 
            equippable=True,
            armor_bonus=0,  # No damage reduction
            dodge_bonus=5   # Improves dodge
        )
        return Entity(x, y, '>', LIGHT_BLUE, EntityType.ITEM, 'Boots', blocks=False, item=item_component)
    
    elif item_name == 'gloves':
        item_component = Item(
            item_type=ItemType.GLOVES, 
            equippable=True,
            armor_bonus=1,  # Small damage reduction
            dodge_bonus=0   # No dodge effect
        )
        return Entity(x, y, '=', LIGHT_BLUE, EntityType.ITEM, 'Gloves', blocks=False, item=item_component)
    
    elif item_name == 'shield':
        item_component = Item(
            item_type=ItemType.SHIELD, 
            equippable=True,
            armor_bonus=1,  # Small damage reduction
            dodge_bonus=5   # Improves dodge
        )
        return Entity(x, y, '[', LIGHT_BLUE, EntityType.ITEM, 'Shield', blocks=False, item=item_component)
    
    # If we didn't find the item
    return None
