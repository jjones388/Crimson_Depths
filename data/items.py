import random
from ..config import EntityType, ItemType, WHITE, YELLOW, LIGHT_BLUE
from ..entities.entity import Entity
from ..entities.components.item import Item, heal_player
from .monsters import MONSTERS
from ..entities.components.ai import BasicMonster
from ..entities.components.fighter import Fighter

# Define weapon data structure
class WeaponData:
    def __init__(self, name, weapon_type, damage_type, size, damage_dice):
        self.name = name
        self.weapon_type = weapon_type
        self.damage_type = damage_type
        self.size = size  # 'S', 'M', or 'L'
        self.damage_dice = damage_dice  # tuple of (count, sides)
        
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
}

def place_entities(room, entities, max_enemies_per_room, max_items_per_room, dungeon_level=1):
    # Random number of enemies
    number_of_enemies = random.randint(0, max_enemies_per_room)
    
    # Random number of items
    number_of_items = random.randint(0, max_items_per_room)
    
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
                    ac=monster_data.ac,
                    damage_dice=monster_data.damage_dice
                )
                
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
                    # 80% chance for an orc - 1d4 HP, AC 11, 1d4 damage
                    fighter_component = Fighter(
                        hp=random.randint(1, 4),  # 1d4 HP
                        ac=11,  # AC 11
                        damage_dice=(1, 4)  # 1d4 damage
                    )
                    ai_component = BasicMonster()
                    enemy = Entity(x, y, 'o', WHITE, EntityType.ENEMY, 'Orc', blocks=True, 
                                  fighter=fighter_component, ai=ai_component)
                else:
                    # 20% chance for a troll - 1d8, AC 13, 1d6 damage
                    fighter_component = Fighter(
                        hp=random.randint(1, 8),  # 1d8 HP
                        ac=13,  # AC 13
                        damage_dice=(1, 6)  # 1d6 damage
                    )
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
            
            if item_choice < 0.4:  # 40% chance for healing potion
                item_component = Item(use_function=heal_player, item_type=ItemType.CONSUMABLE)
                item = Entity(x, y, '!', YELLOW, EntityType.ITEM, 'Healing Potion', blocks=False, item=item_component)
            elif item_choice < 0.7:  # 30% chance for a weapon
                # Choose a random weapon
                weapon_key = random.choice(list(WEAPONS.keys()))
                weapon = WEAPONS[weapon_key]
                
                item_component = Item(
                    item_type=ItemType.WEAPON, 
                    equippable=True,
                    damage_dice=weapon.damage_dice,
                    weapon_data=weapon
                )
                
                # Use '/' for all melee weapons (ASCII value 47 in CP437)
                char = '/'
                
                item = Entity(x, y, char, WHITE, EntityType.ITEM, weapon.name, blocks=False, item=item_component)
            elif item_choice < 0.8:  # 10% chance for a shield
                item_component = Item(
                    item_type=ItemType.SHIELD, 
                    equippable=True,
                    ac_bonus=1  # +1 AC
                )
                item = Entity(x, y, '[', WHITE, EntityType.ITEM, 'Shield', blocks=False, item=item_component)
            elif item_choice < 0.85:  # 5% chance for a helmet
                item_component = Item(
                    item_type=ItemType.HELMET, 
                    equippable=True,
                    ac_bonus=1  # +1 AC
                )
                item = Entity(x, y, '^', LIGHT_BLUE, EntityType.ITEM, 'Helmet', blocks=False, item=item_component)
            elif item_choice < 0.95:  # 10% chance for armor
                item_component = Item(
                    item_type=ItemType.ARMOR, 
                    equippable=True,
                    ac_bonus=4  # +4 AC (chainmail makes AC 15)
                )
                item = Entity(x, y, '#', LIGHT_BLUE, EntityType.ITEM, 'Chainmail', blocks=False, item=item_component)
            else:  # 5% chance for boots
                item_component = Item(
                    item_type=ItemType.BOOTS, 
                    equippable=True,
                    ac_bonus=1  # +1 AC
                )
                item = Entity(x, y, '>', LIGHT_BLUE, EntityType.ITEM, 'Boots', blocks=False, item=item_component)
            
            entities.append(item)
