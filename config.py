import pygame
import numpy as np
from enum import Enum
import os

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 16  # Size of each tile in pixels
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# GUI Layout Constants
INFO_PANEL_WIDTH = 16  # Width in tiles for the right panel
MESSAGE_LOG_HEIGHT = 8  # Height in tiles for the message log
LEFT_PANEL_WIDTH = (SCREEN_WIDTH // TILE_SIZE) - INFO_PANEL_WIDTH
MAP_VIEW_WIDTH = LEFT_PANEL_WIDTH - 2  # -2 for borders
MAP_VIEW_HEIGHT = (SCREEN_HEIGHT // TILE_SIZE) - MESSAGE_LOG_HEIGHT - 2  # -2 for borders

# Calculate pixel positions
INFO_PANEL_X = (LEFT_PANEL_WIDTH) * TILE_SIZE
MESSAGE_LOG_Y = (SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE)

# Game map dimensions
MAP_WIDTH = 90  # Width of the game map in tiles
MAP_HEIGHT = 60  # Height of the game map in tiles
MAX_ROOMS = 30
MIN_ROOM_SIZE = 6
MAX_ROOM_SIZE = 15
MAX_ENEMIES_PER_ROOM = 3
MAX_ITEMS_PER_ROOM = 2

# Message log settings
MAX_MESSAGES = 50

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (173, 216, 230)

# Border character indices in CP437
BORDER_HORIZONTAL = 205  # ═
BORDER_VERTICAL = 186    # ║
BORDER_TOP_LEFT = 201    # ╔
BORDER_TOP_RIGHT = 187   # ╗
BORDER_BOTTOM_LEFT = 200 # ╚
BORDER_BOTTOM_RIGHT = 188 # ╝
BORDER_T_LEFT = 204      # ╠
BORDER_T_RIGHT = 185     # ╣
BORDER_T_UP = 202        # ╩
BORDER_T_DOWN = 203      # ╦
BORDER_CROSS = 206       # ╬

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Roguelike Game")

# Load the CP437 tileset using an absolute path
tileset_path = os.path.join(current_dir, 'cp437_16x16.png')
tileset = pygame.image.load(tileset_path).convert_alpha()

# Tile types
class TileType(Enum):
    WALL = 0
    FLOOR = 1
    CORRIDOR = 2
    STAIRS_DOWN = 3
    STAIRS_UP = 4

# Entity types
class EntityType(Enum):
    PLAYER = 0
    ENEMY = 1
    ITEM = 2

class EquipmentSlot(Enum):
    RIGHT_HAND = 0
    LEFT_HAND = 1
    HEAD = 2
    TORSO = 3
    LEGS = 4
    HANDS = 5
    FEET = 6

class ItemType(Enum):
    WEAPON = 0
    SHIELD = 1
    HELMET = 2
    ARMOR = 3
    LEG_ARMOR = 4
    GLOVES = 5
    BOOTS = 6
    CONSUMABLE = 7
    KEY = 8
    MISC = 9

def get_tile_from_tileset(index):
    # Calculate position in the tileset
    x = index % 16
    y = index // 16
    # Extract the tile from the tileset
    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    image.blit(tileset, (0, 0), rect)
    return image
