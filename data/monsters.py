import random

class MonsterData:
    def __init__(self, char, name, hit_dice, armor, damage_dice, xp, min_level, max_level, dodge=10):
        self.char = char                # Character representation
        self.name = name                # Monster name
        self.hit_dice = hit_dice        # Tuple of (count, dice_sides) or a fraction
        self.armor = armor              # Damage reduction (formerly AC)
        self.dodge = dodge              # Dodge chance
        self.damage_dice = damage_dice  # Tuple of (count, dice_sides)
        self.xp = xp                    # XP awarded
        self.min_level = min_level      # Minimum dungeon level
        self.max_level = max_level      # Maximum dungeon level
    
    def roll_hit_points(self):
        """Roll hit points based on hit dice"""
        if isinstance(self.hit_dice, tuple):
            dice_count, dice_sides = self.hit_dice
            return sum(random.randint(1, dice_sides) for _ in range(dice_count))
        elif self.hit_dice == 0.5:  # 1/2 HD
            return random.randint(1, 4)
        elif self.hit_dice == 0.25:  # 1/4 HD
            return random.randint(1, 3)
        else:
            raise ValueError(f"Invalid hit dice value: {self.hit_dice}")

# Define all monsters
MONSTERS = {
    # Lowercase monsters (a-z)
    'a': MonsterData('a', 'Ant', 0.5, 12, (1, 3), 25, 1, 3),
    'b': MonsterData('b', 'Bat', 0.5, 12, (1, 2), 25, 1, 3),
    'c': MonsterData('c', 'Cobra', 1, 11, (1, 4), 50, 2, 5),
    'd': MonsterData('d', 'Wild Dog', 1, 12, (1, 4), 50, 1, 4),
    'e': MonsterData('e', 'Eel', 0.5, 11, (1, 3), 25, 1, 3),
    'f': MonsterData('f', 'Giant Frog', 1, 11, (1, 4), 50, 1, 4),
    'g': MonsterData('g', 'Goblin', 1, 12, (1, 6), 50, 1, 5),
    'h': MonsterData('h', 'Hawk', 0.5, 13, (1, 3), 35, 2, 4),
    'i': MonsterData('i', 'Imp', 1, 13, (1, 4), 60, 3, 6),
    'j': MonsterData('j', 'Jackal', 0.5, 12, (1, 4), 35, 1, 4),
    'k': MonsterData('k', 'Kobold', 0.5, 12, (1, 4), 35, 1, 5),
    'l': MonsterData('l', 'Giant Lizard', 1, 13, (1, 6), 60, 2, 5),
    'm': MonsterData('m', 'Mold', 0.5, 8, (1, 6), 40, 1, 6),
    'n': MonsterData('n', 'Newt', 0.25, 11, (1, 2), 15, 1, 2),
    'o': MonsterData('o', 'Orc', 1, 11, (1, 6), 50, 1, 7),
    'p': MonsterData('p', 'Piranha', 0.5, 12, (1, 4), 40, 2, 5),
    'q': MonsterData('q', 'Quasit', 1, 13, (1, 4), 65, 4, 7),
    'r': MonsterData('r', 'Giant Rat', 0.5, 11, (1, 3), 25, 1, 4),
    's': MonsterData('s', 'Snake', 1, 12, (1, 4), 55, 2, 6),
    't': MonsterData('t', 'Giant Tick', 1, 12, (1, 4), 55, 3, 7),
    'u': MonsterData('u', 'Minor Undead', 1, 11, (1, 4), 55, 3, 8),
    'v': MonsterData('v', 'Viper', 1, 12, (1, 4), 65, 3, 7),
    'w': MonsterData('w', 'Dire Weasel', 1, 13, (1, 4), 55, 3, 6),
    'x': MonsterData('x', 'Minor Xorn', (2, 8), 14, (1, 6), 80, 5, 9),
    'y': MonsterData('y', 'Yelper', 1, 12, (1, 4), 50, 2, 5),
    'z': MonsterData('z', 'Minor Zombie', 1, 10, (1, 6), 60, 3, 9),
    
    # Uppercase monsters (A-Z)
    'A': MonsterData('A', 'Auroch', (3, 8), 13, (2, 6), 150, 6, 10),
    'B': MonsterData('B', 'Basilisk', (4, 8), 15, (1, 8), 200, 8, 12),
    'C': MonsterData('C', 'Cyclops', (6, 8), 14, (2, 8), 300, 10, 14),
    'D': MonsterData('D', 'Young Dragon', (8, 8), 16, (2, 6), 600, 12, 16),
    'E': MonsterData('E', 'Elemental', (4, 8), 15, (2, 6), 250, 8, 12),
    'F': MonsterData('F', 'Frost Giant', (7, 8), 15, (2, 8), 450, 11, 15),
    'G': MonsterData('G', 'Golem', (6, 8), 16, (2, 8), 400, 10, 15),
    'H': MonsterData('H', 'Hydra', (5, 8), 15, (2, 6), 350, 9, 14),
    'I': MonsterData('I', 'Iron Golem', (10, 8), 18, (3, 6), 800, 15, 20),
    'J': MonsterData('J', 'Jabberwock', (7, 8), 15, (2, 6), 500, 12, 17),
    'K': MonsterData('K', 'Kraken', (9, 8), 16, (2, 8), 700, 14, 19),
    'L': MonsterData('L', 'Lich', (10, 8), 17, (2, 8), 1000, 16, 20),
    'M': MonsterData('M', 'Minotaur', (5, 8), 14, (2, 6), 300, 8, 13),
    'N': MonsterData('N', 'Naga', (6, 8), 15, (2, 4), 350, 9, 14),
    'O': MonsterData('O', 'Ogre', (4, 8), 14, (2, 6), 200, 7, 12),
    'P': MonsterData('P', 'Purple Worm', (8, 8), 16, (2, 8), 650, 13, 18),
    'Q': MonsterData('Q', 'Quetzalcoatl', (9, 8), 17, (2, 8), 800, 15, 20),
    'R': MonsterData('R', 'Roper', (7, 8), 16, (2, 6), 450, 11, 16),
    'S': MonsterData('S', 'Sphinx', (8, 8), 17, (2, 6), 600, 13, 18),
    'T': MonsterData('T', 'Troll', (3, 8), 14, (1, 8), 150, 6, 11),
    'U': MonsterData('U', 'Umber Hulk', (6, 8), 15, (2, 6), 400, 10, 15),
    'V': MonsterData('V', 'Vampire', (8, 8), 16, (2, 6), 700, 14, 19),
    'W': MonsterData('W', 'Wyvern', (7, 8), 15, (2, 6), 500, 12, 17),
    'X': MonsterData('X', 'Xorn', (5, 8), 16, (2, 6), 350, 9, 14),
    'Y': MonsterData('Y', 'Yeti', (4, 8), 14, (2, 4), 200, 8, 13),
    'Z': MonsterData('Z', 'Zombie Dragon', (10, 8), 18, (3, 6), 1200, 17, 20),
}
