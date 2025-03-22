import pygame
from ..config import (
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, YELLOW, LIGHT_BLUE,
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, LEFT_PANEL_WIDTH, MESSAGE_LOG_HEIGHT,
    INFO_PANEL_WIDTH, INFO_PANEL_X, MESSAGE_LOG_Y, MAP_HEIGHT, MAP_WIDTH,
    BORDER_HORIZONTAL, BORDER_VERTICAL, BORDER_TOP_LEFT, BORDER_TOP_RIGHT,
    BORDER_BOTTOM_LEFT, BORDER_BOTTOM_RIGHT, BORDER_T_LEFT, BORDER_T_RIGHT,
    BORDER_T_UP, BORDER_T_DOWN, BORDER_CROSS, TileType, EntityType, EquipmentSlot,
    get_tile_from_tileset, screen
)

def draw_borders():
    """Draw borders around the three UI areas using double-line characters"""
    # Get tile images for borders
    h_border = get_tile_from_tileset(BORDER_HORIZONTAL)
    v_border = get_tile_from_tileset(BORDER_VERTICAL)
    tl_corner = get_tile_from_tileset(BORDER_TOP_LEFT)
    tr_corner = get_tile_from_tileset(BORDER_TOP_RIGHT)
    bl_corner = get_tile_from_tileset(BORDER_BOTTOM_LEFT)
    br_corner = get_tile_from_tileset(BORDER_BOTTOM_RIGHT)
    t_left = get_tile_from_tileset(BORDER_T_LEFT)
    t_right = get_tile_from_tileset(BORDER_T_RIGHT)
    t_up = get_tile_from_tileset(BORDER_T_UP)
    t_down = get_tile_from_tileset(BORDER_T_DOWN)
    cross = get_tile_from_tileset(BORDER_CROSS)
    
    # Color borders white
    for tile in [h_border, v_border, tl_corner, tr_corner, bl_corner, br_corner, 
                t_left, t_right, t_up, t_down, cross]:
        tile.fill(WHITE, special_flags=pygame.BLEND_RGBA_MULT)
    
    # Calculate panel positions
    left_panel_width = SCREEN_WIDTH - (INFO_PANEL_WIDTH * TILE_SIZE)
    
    # Top border of both panels
    for x in range(SCREEN_WIDTH // TILE_SIZE):
        screen.blit(h_border, (x * TILE_SIZE, 0))
    
    # Bottom border of both panels
    for x in range(SCREEN_WIDTH // TILE_SIZE):
        screen.blit(h_border, (x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE))
    
    # Left border of left panel
    for y in range(1, SCREEN_HEIGHT // TILE_SIZE - 1):
        screen.blit(v_border, (0, y * TILE_SIZE))
    
    # Right border of right panel
    for y in range(1, SCREEN_HEIGHT // TILE_SIZE - 1):
        screen.blit(v_border, (SCREEN_WIDTH - TILE_SIZE, y * TILE_SIZE))
    
    # Vertical divider between left and right panels
    for y in range(1, SCREEN_HEIGHT // TILE_SIZE - 1):
        screen.blit(v_border, (left_panel_width - TILE_SIZE, y * TILE_SIZE))
    
    # Horizontal divider between Map View and Message Log
    for x in range(1, left_panel_width // TILE_SIZE - 1):
        screen.blit(h_border, (x * TILE_SIZE, SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE))
    
    # Corner pieces
    screen.blit(tl_corner, (0, 0))  # Top-left of screen
    screen.blit(tr_corner, (SCREEN_WIDTH - TILE_SIZE, 0))  # Top-right of screen
    screen.blit(bl_corner, (0, SCREEN_HEIGHT - TILE_SIZE))  # Bottom-left of screen
    screen.blit(br_corner, (SCREEN_WIDTH - TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE))  # Bottom-right of screen
    
    # T-junctions
    # T-junction for top of vertical divider
    screen.blit(t_down, (left_panel_width - TILE_SIZE, 0))  
    
    # T-junction for bottom of vertical divider
    screen.blit(t_up, (left_panel_width - TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE))  
    
    # T-junction for left of horizontal divider
    screen.blit(t_right, (0, SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE))  
    
    # T-junction for right of horizontal divider
    screen.blit(t_left, (left_panel_width - TILE_SIZE, SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE))

def draw_map(game_map, offset_x, offset_y):
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            screen_x = (x - offset_x) * TILE_SIZE + TILE_SIZE
            screen_y = (y - offset_y) * TILE_SIZE + TILE_SIZE
            
            # Check if the tile is within the visible Map View area
            if (screen_x < TILE_SIZE or screen_x >= LEFT_PANEL_WIDTH * TILE_SIZE - TILE_SIZE or 
                screen_y < TILE_SIZE or screen_y >= SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE):
                continue
            
            visible = game_map.visible[y][x]
            explored = game_map.explored[y][x]
            
            if not explored:
                # Unexplored areas are completely black
                continue
            
            tile_index = 0
            tile_color = WHITE
            
            if game_map.tiles[y][x] == TileType.WALL:
                tile_index = 219  # Block character (█)
                tile_color = GRAY
            elif game_map.tiles[y][x] == TileType.FLOOR or game_map.tiles[y][x] == TileType.CORRIDOR:
                tile_index = 250  # Dot character (·)
                tile_color = WHITE
            elif game_map.tiles[y][x] == TileType.STAIRS_DOWN:
                tile_index = 62  # > character
                tile_color = WHITE
            elif game_map.tiles[y][x] == TileType.STAIRS_UP:
                tile_index = 60  # < character
                tile_color = WHITE
            
            # If it's not visible but explored, darken the color
            if not visible:
                # Darken the color by multiplying by 0.5
                tile_color = tuple(c // 2 for c in tile_color)
            
            tile = get_tile_from_tileset(tile_index)
            colored_tile = tile.copy()
            colored_tile.fill(tile_color, special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(colored_tile, (screen_x, screen_y))

def draw_entities(entities, game_map, offset_x, offset_y):
    # Custom sort key function: Draw items first, then corpses, then living monsters, then player
    def entity_sort_key(e):
        if e.entity_type == EntityType.ITEM:
            return 0  # Items drawn first
        elif e.entity_type == EntityType.ENEMY and e.char == '%':
            return 1  # Corpses drawn second
        elif e.entity_type == EntityType.ENEMY:
            return 2  # Living monsters drawn third
        else:
            return 3  # Player drawn last
    
    sorted_entities = sorted(entities, key=entity_sort_key)
    
    for entity in sorted_entities:
        screen_x = (entity.x - offset_x) * TILE_SIZE + TILE_SIZE
        screen_y = (entity.y - offset_y) * TILE_SIZE + TILE_SIZE
        
        # Check if the entity is within the visible Map View area
        if (screen_x < TILE_SIZE or screen_x >= LEFT_PANEL_WIDTH * TILE_SIZE - TILE_SIZE or 
            screen_y < TILE_SIZE or screen_y >= SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE):
            continue
            
        # Only draw entities that are in the field of vision
        if entity.entity_type == EntityType.PLAYER or game_map.visible[entity.y][entity.x]:
            if entity.entity_type == EntityType.PLAYER:
                tile_index = 64  # @ character
            else:
                tile_index = ord(entity.char)
            
            tile = get_tile_from_tileset(tile_index)
            colored_tile = tile.copy()
            colored_tile.fill(entity.color, special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(colored_tile, (screen_x, screen_y))

def draw_info_panel(player, game_world):
    # Draw info panel in the right section
    panel_x = LEFT_PANEL_WIDTH * TILE_SIZE
    panel_width = INFO_PANEL_WIDTH * TILE_SIZE
    font = pygame.font.SysFont('Arial', 14)
    small_font = pygame.font.SysFont('Arial', 12)
    
    # Title
    title_text = font.render("CHARACTER INFO", True, YELLOW)
    title_x = panel_x + (panel_width - title_text.get_width()) // 2
    screen.blit(title_text, (title_x, TILE_SIZE * 1))
    
    # Horizontal line below title
    for x in range(INFO_PANEL_WIDTH - 2):
        screen.blit(get_tile_from_tileset(196), (panel_x + (x + 1) * TILE_SIZE, TILE_SIZE * 2))
    
    # Dungeon level and character level
    level_y = TILE_SIZE * 2.5
    dungeon_text = font.render(f"Dungeon: {game_world.current_level}", True, LIGHT_BLUE)
    screen.blit(dungeon_text, (panel_x + TILE_SIZE, level_y))
    
    char_level_text = font.render(f"Level: {player.fighter.level}", True, LIGHT_BLUE)
    screen.blit(char_level_text, (panel_x + panel_width // 2, level_y))
    
    # Experience points
    xp_y = level_y + TILE_SIZE * 1.2
    xp_text = font.render(f"XP: {player.fighter.xp}", True, WHITE)
    screen.blit(xp_text, (panel_x + TILE_SIZE, xp_y))
    
    # XP for next level
    next_level_xp = player.fighter.get_next_level_xp()
    if next_level_xp:
        next_level_text = small_font.render(f"Next: {next_level_xp}", True, GRAY)
        screen.blit(next_level_text, (panel_x + panel_width // 2, xp_y))
    
    # Health
    hp_y = xp_y + TILE_SIZE * 1.5
    hp_text = font.render(f"HP: {player.fighter.hp}/{player.fighter.max_hp}", True, WHITE)
    screen.blit(hp_text, (panel_x + TILE_SIZE, hp_y))
    
    # Health bar
    bar_width = panel_width - 4 * TILE_SIZE
    bar_height = TILE_SIZE - 4
    bar_x = panel_x + 2 * TILE_SIZE
    bar_y = hp_y + TILE_SIZE
    
    # Draw background rectangle
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
    
    # Calculate width of the health bar
    hp_ratio = player.fighter.hp / player.fighter.max_hp
    filled_width = int(bar_width * hp_ratio)
    
    # Draw the filled portion of the bar
    pygame.draw.rect(screen, RED, (bar_x, bar_y, filled_width, bar_height))
    
    # Combat stats
    combat_y = hp_y + TILE_SIZE * 2
    combat_text = [
        f"AC: {player.fighter.ac}",
        f"Attack: +{player.fighter.attack_bonus}",
        f"Damage: {player.fighter.damage_dice[0]}d{player.fighter.damage_dice[1]}"
    ]
    
    for i, text in enumerate(combat_text):
        stat_text = font.render(text, True, WHITE)
        screen.blit(stat_text, (panel_x + TILE_SIZE, combat_y + i * TILE_SIZE * 1.2))
    
    # Character stats
    char_stats_y = combat_y + TILE_SIZE * 4
    char_stats_title = font.render("STATS", True, YELLOW)
    char_stats_x = panel_x + (panel_width - char_stats_title.get_width()) // 2
    screen.blit(char_stats_title, (char_stats_x, char_stats_y))
    
    # Horizontal line below stats title
    for x in range(INFO_PANEL_WIDTH - 2):
        screen.blit(get_tile_from_tileset(196), (panel_x + (x + 1) * TILE_SIZE, char_stats_y + TILE_SIZE))
    
    # Stats list - display in two columns
    char_stats = [
        ("STR", player.fighter.str),
        ("INT", player.fighter.int),
        ("WIS", player.fighter.wis),
        ("DEX", player.fighter.dex),
        ("CON", player.fighter.con),
        ("CHA", player.fighter.cha)
    ]
    
    col_width = panel_width // 2
    for i, (stat_name, stat_value) in enumerate(char_stats):
        # Calculate position (2 columns, 3 rows)
        col = i // 3
        row = i % 3
        x_pos = panel_x + col * col_width + TILE_SIZE
        y_pos = char_stats_y + TILE_SIZE * 2 + row * TILE_SIZE * 1.2
        
        stat_text = font.render(f"{stat_name}: {stat_value}", True, WHITE)
        screen.blit(stat_text, (x_pos, y_pos))
    
    # Controls section
    controls_y = char_stats_y + TILE_SIZE * 5.5
    controls_title = font.render("CONTROLS", True, YELLOW)
    controls_x = panel_x + (panel_width - controls_title.get_width()) // 2
    screen.blit(controls_title, (controls_x, controls_y))
    
    # Horizontal line below controls title
    for x in range(INFO_PANEL_WIDTH - 2):
        screen.blit(get_tile_from_tileset(196), (panel_x + (x + 1) * TILE_SIZE, controls_y + TILE_SIZE))
    
    # Controls list
    controls_text = [
        "Arrow Keys: Move",
        "H: Use potion",
        "I: Inventory",
        ">: Go down stairs",
        "<: Go up stairs",
        "ESC: Quit"
    ]
    
    for i, text in enumerate(controls_text):
        control_text = small_font.render(text, True, WHITE)
        screen.blit(control_text, (panel_x + TILE_SIZE, controls_y + TILE_SIZE * 2 + i * TILE_SIZE))

def draw_message_log(message_log):
    # Draw message log at the bottom
    log_x = TILE_SIZE
    log_y = SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE
    log_width = LEFT_PANEL_WIDTH * TILE_SIZE - (2 * TILE_SIZE)
    log_height = MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE  # Subtract one tile for the bottom border
    
    font = pygame.font.SysFont('Arial', 14)
    line_height = font.get_linesize()
    
    # Draw background
    pygame.draw.rect(screen, BLACK, (log_x, log_y, log_width, log_height))
    
    # Calculate how many messages we can display
    max_messages_visible = int(log_height / line_height)
    
    # Display the most recent messages
    start_y = log_y
    messages_to_draw = list(message_log.messages)[-max_messages_visible:]
    
    for message, color in messages_to_draw:
        text = font.render(message, True, color)
        screen.blit(text, (log_x + 5, start_y))
        start_y += line_height

def draw_inventory(player, selected_index, inventory_mode, selected_equipment_slot):
    """Draw the inventory screen"""
    # Create a semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    # Draw inventory title
    font_title = pygame.font.SysFont('Arial', 24)
    title_text = font_title.render("INVENTORY", True, YELLOW)
    title_x = (LEFT_PANEL_WIDTH * TILE_SIZE) // 2 - title_text.get_width() // 2
    screen.blit(title_text, (title_x, TILE_SIZE * 2))
    
    # Draw equipment section title
    equip_title = font_title.render("EQUIPMENT", True, LIGHT_BLUE if inventory_mode == 'equipment' else GRAY)
    equip_x = TILE_SIZE * 4
    screen.blit(equip_title, (equip_x, TILE_SIZE * 4))
    
    # Draw inventory section title
    inv_title = font_title.render("ITEMS", True, LIGHT_BLUE if inventory_mode == 'items' else GRAY)
    inv_x = (LEFT_PANEL_WIDTH * TILE_SIZE) // 2 + TILE_SIZE * 4
    screen.blit(inv_title, (inv_x, TILE_SIZE * 4))
    
    # Draw dividing line
    mid_x = (LEFT_PANEL_WIDTH * TILE_SIZE) // 2
    pygame.draw.line(screen, WHITE, (mid_x, TILE_SIZE * 6), 
                    (mid_x, SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE * 2), 2)
    
    # Font for items
    font = pygame.font.SysFont('Arial', 16)
    small_font = pygame.font.SysFont('Arial', 12)
    
    # Draw equipment slots
    equipment_slots = [
        (EquipmentSlot.RIGHT_HAND, "Right Hand"),
        (EquipmentSlot.LEFT_HAND, "Left Hand"),
        (EquipmentSlot.HEAD, "Head"),
        (EquipmentSlot.TORSO, "Torso"),
        (EquipmentSlot.LEGS, "Legs"),
        (EquipmentSlot.HANDS, "Hands"),
        (EquipmentSlot.FEET, "Feet")
    ]
    
    # Track if we're showing a two-handed weapon
    two_handed_weapon = None
    
    for i, (slot, name) in enumerate(equipment_slots):
        # Draw slot name
        y_pos = TILE_SIZE * 6 + i * TILE_SIZE * 2
        slot_text = font.render(name + ":", True, WHITE)
        screen.blit(slot_text, (TILE_SIZE * 2, y_pos))
        
        # Get equipped item for this slot
        equipped_item = player.inventory.get_equipped_item(slot)
        
        # Draw highlight for selected equipment slot
        if inventory_mode == 'equipment' and slot == selected_equipment_slot:
            pygame.draw.rect(screen, (50, 50, 150), 
                          (TILE_SIZE, y_pos - 5, 
                           mid_x - TILE_SIZE * 2, 
                           TILE_SIZE * 1.5))
        
        # Draw equipped item or "Empty"
        if equipped_item:
            # Check if it's a two-handed weapon
            is_two_handed = (equipped_item.item.weapon_data and equipped_item.item.weapon_data.is_two_handed)
            
            # If this is the left hand slot and we already displayed a two-handed weapon in the right hand
            if slot == EquipmentSlot.LEFT_HAND and two_handed_weapon:
                info_text = font.render(f"(Same as right hand - {two_handed_weapon.name})", True, GRAY)
                screen.blit(info_text, (TILE_SIZE * 14, y_pos))
                continue
                
            # Draw item character
            item_char = get_tile_from_tileset(ord(equipped_item.char))
            colored_char = item_char.copy()
            colored_char.fill(equipped_item.color, special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(colored_char, (TILE_SIZE * 12, y_pos))
            
            # Add (2H) suffix for two-handed weapons
            if is_two_handed:
                item_text = font.render(f"{equipped_item.name} (2H)", True, YELLOW)
                # Remember we displayed a two-handed weapon
                two_handed_weapon = equipped_item
            else:
                item_text = font.render(equipped_item.name, True, YELLOW)
            
            screen.blit(item_text, (TILE_SIZE * 14, y_pos))
        else:
            item_text = font.render("Empty", True, GRAY)
            screen.blit(item_text, (TILE_SIZE * 14, y_pos))
    
    # Draw carried items (right column)
    items_start_y = TILE_SIZE * 6
    items_per_page = 10
    
    # Draw slot count at bottom right
    slot_text = font.render(f"Slots: {len(player.inventory.items)}/{player.inventory.capacity}", True, WHITE)
    slot_x = LEFT_PANEL_WIDTH * TILE_SIZE - slot_text.get_width() - TILE_SIZE
    slot_y = SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE * 2
    screen.blit(slot_text, (slot_x, slot_y))
    
    for i, item in enumerate(player.inventory.items[:items_per_page]):
        y_pos = items_start_y + i * TILE_SIZE * 2
        
        # Highlight selected item
        if inventory_mode == 'items' and i == selected_index:
            pygame.draw.rect(screen, (50, 50, 150), 
                           (mid_x + TILE_SIZE, y_pos - 5, 
                            LEFT_PANEL_WIDTH * TILE_SIZE // 2 - TILE_SIZE * 2, 
                            TILE_SIZE * 1.5))
        
        # Draw item character and name
        item_char = get_tile_from_tileset(ord(item.char))
        colored_char = item_char.copy()
        colored_char.fill(item.color, special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(colored_char, (mid_x + TILE_SIZE * 2, y_pos))
        
        # Add (2H) suffix for two-handed weapons
        if item.item and item.item.weapon_data and item.item.weapon_data.is_two_handed:
            item_text = font.render(f"{item.name} (2H)", True, WHITE)
        else:
            item_text = font.render(item.name, True, WHITE)
            
        screen.blit(item_text, (mid_x + TILE_SIZE * 4, y_pos))
    
    # Draw instructions
    instructions = [
        "←/→: Switch sides",
        "↑/↓: Navigate",
        "Enter: Use/Equip/Unequip",
        "D: Drop item",
        "I: Close inventory"
    ]
    
    for i, instruction in enumerate(instructions):
        instr_text = font.render(instruction, True, LIGHT_BLUE)
        screen.blit(instr_text, (LEFT_PANEL_WIDTH * TILE_SIZE // 4, 
                               SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE - TILE_SIZE * (6-i)))
