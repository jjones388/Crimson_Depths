import pygame
import sys
import random
from config import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, LEFT_PANEL_WIDTH, MESSAGE_LOG_HEIGHT,
    INFO_PANEL_WIDTH, MAP_WIDTH, MAP_HEIGHT, BLACK, WHITE, RED, GREEN, LIGHT_BLUE, YELLOW,
    UI_BACKGROUND, UI_TEXT_PRIMARY, screen, EntityType, EquipmentSlot, ItemType
)
from map.map import Map
from map.fov import calculate_fov
from entities.entity import Entity
from entities.components.fighter import Fighter
from entities.components.ai import BasicMonster
from entities.components.item import Item, heal_player
from entities.inventory import Inventory
from game.world import GameWorld
from data.items import place_entities, create_item
from ui.message_log import MessageLog
from ui.theme import ThemeManager
from ui.rendering import (
    draw_game_ui, draw_borders, draw_map, draw_entities, draw_info_panel, 
    draw_message_log, draw_inventory, draw_targeting_cursor, draw_arrow_path
)
from ui.title_screen import title_screen
from data.monsters import MONSTERS
from map.town import BuildingType

def main():
    # Initialize game variables
    game_world = None
    player = None
    message_log = None
    entities = None
    game_map = None
    game_state = None
    game_over_time = None
    inventory_index = None
    inventory_mode = None
    selected_equipment_slot = None
    fov_radius = None
    fov_recompute = None
    
    # Initial game setup or resume from title screen
    while True:
        # Show the title screen
        # If we have a player, that means we're coming from the game, so show resume option
        choice = title_screen(show_resume=player is not None and player.fighter.hp > 0)
        
        # Initialize or reset the game based on choice
        if choice == "new_game":
            # Create new game
            game_world = GameWorld(max_levels=20)
            
            # Create message log
            message_log = MessageLog()
            message_log.add_message("Welcome to Crimson Depths! Use arrow keys to move.", LIGHT_BLUE)
            message_log.add_message("Find the stairs (>) to descend into the dungeon.", LIGHT_BLUE)
            message_log.add_message("Press I to open inventory.", LIGHT_BLUE)
            message_log.add_message("Press T for targeted fire or F for quick fire with ranged weapons.", LIGHT_BLUE)
            message_log.add_message("Press E to auto-explore the dungeon (stops when encountering monsters).", LIGHT_BLUE)
            
            # Create inventory for player
            inventory_component = Inventory()
            
            # Create player with OSR-style stats
            fighter_component = Fighter(hp=8, armor=2, damage_dice=(1, 3))
            player = Entity(0, 0, '@', WHITE, EntityType.PLAYER, 'Player', blocks=True, 
                          fighter=fighter_component, inventory=inventory_component, silver_pieces=50)
            
            # Initialize town level
            game_map, level_entities = game_world.get_current_level()
            
            # Place player in the town - at the center near the dungeon stairs
            if game_map.down_stairs_position:
                player.x = game_map.down_stairs_position[0]
                player.y = game_map.down_stairs_position[1] - 2  # Place player near but not on the stairs
            else:
                # Fallback to center of map
                player.x = MAP_WIDTH // 2
                player.y = MAP_HEIGHT // 2
            
            # Add player to entities list
            entities = [player] + level_entities
            game_map.entities = entities
            
            # Add starting equipment (shortbow and arrows)
            # Create and add shortbow
            shortbow = create_item('shortbow', player.x, player.y)
            player.inventory.add_item(shortbow, message_log)
            player.inventory.equip_item(shortbow, EquipmentSlot.RIGHT_HAND, message_log, entities)
            
            # Create and add arrows
            arrows = create_item('arrows', player.x, player.y)
            player.inventory.add_item(arrows, message_log)
            player.inventory.equip_item(arrows, EquipmentSlot.LEFT_HAND, message_log, entities)
            
            # Game state
            game_state = 'playing'  # Can be 'playing', 'inventory', 'targeting', or 'dead'
            game_over_time = None
            inventory_index = 0  # Currently selected inventory item
            inventory_mode = 'items'  # Can be 'items' or 'equipment'
            selected_equipment_slot = EquipmentSlot.RIGHT_HAND  # Currently selected equipment slot
            
            # FOV setup
            fov_radius = 20 if game_world.current_level == 0 else 10  # Double FOV in town
            fov_recompute = True
            
            # Initial FOV calculation before game starts
            calculate_fov(game_map, player.x, player.y, fov_radius)
        
        elif choice == "resume_game" and player is not None and player.fighter.hp > 0:
            # Resume game - all variables should already be set
            # Make sure we're on the correct dungeon level
            game_map, level_entities = game_world.get_current_level()
            entities = [player] + level_entities
            game_map.entities = entities
            # Recalculate FOV to be safe
            fov_recompute = True
        
        elif choice != "resume_game":
            # Exit or other unimplemented options
            return
            
        # Play the game
        player_died = play_game(
            game_world, player, message_log, entities, game_map,
            game_state, game_over_time, inventory_index, inventory_mode,
            selected_equipment_slot, fov_radius, fov_recompute
        )
        
        # If the player died, we need to reset the player object so they can't "resume" a dead character
        if player_died:
            player = None

def play_game(
    game_world, player, message_log, entities, game_map,
    game_state, game_over_time, inventory_index, inventory_mode,
    selected_equipment_slot, fov_radius, fov_recompute
):
    """Main game loop extracted to a function to allow returning to title screen"""
    # Define character sheet variables
    selected_attribute = 0
    attributes = ['str', 'int', 'wis', 'dex', 'con', 'cha']
    attribute_names = ['Strength', 'Intelligence', 'Wisdom', 'Dexterity', 'Constitution', 'Charisma']
    
    # Auto-explore variables
    auto_explore = False
    auto_explore_path = []
    auto_explore_target = None
    
    # Camera offsets - adjusted for new layout
    view_width = LEFT_PANEL_WIDTH - 2
    # Calculate view height in tiles: subtract message log rows and action bar rows (5 tiles)
    view_height = (SCREEN_HEIGHT // TILE_SIZE) - MESSAGE_LOG_HEIGHT - 5
    camera_x = max(0, min(MAP_WIDTH - view_width, player.x - view_width // 2))
    camera_y = max(0, min(MAP_HEIGHT - view_height, player.y - view_height // 2))
    
    # Targeting variables
    targeting_x, targeting_y = player.x, player.y
    player.targeting_x = targeting_x  # Store targeting position on player for rendering
    player.targeting_y = targeting_y
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    should_return_to_title = False
    player_died = False  # New flag to track if player died
    
    while running:
        # Limit the frame rate
        clock.tick(60)
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                should_return_to_title = False  # Exit game completely
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == 'targeting':
                        # Cancel targeting mode
                        game_state = 'playing'
                    else:
                        running = False
                        should_return_to_title = True  # Return to title screen
                
                # Enable auto-explore with 'e' key
                if event.key == pygame.K_e and game_state == 'playing':
                    if auto_explore:
                        # Turn off auto-explore
                        auto_explore = False
                        auto_explore_path = []
                        auto_explore_target = None
                        message_log.add_message("Stopped auto-exploration.", LIGHT_BLUE)
                    else:
                        # Turn on auto-explore
                        auto_explore = True
                        auto_explore_path = []
                        auto_explore_target = None
                        message_log.add_message("Started auto-exploration.", LIGHT_BLUE)
                
                # Enter targeting mode for ranged weapons
                if event.key == pygame.K_t and game_state == 'playing':
                    # Check if player has a ranged weapon equipped
                    ranged_weapon = player.inventory.get_equipped_ranged_weapon()
                    if ranged_weapon:
                        # Check if player has arrows equipped
                        if player.inventory.has_ammo_for_weapon():
                            game_state = 'targeting'
                            # Initialize targeting at player position
                            targeting_x, targeting_y = player.x, player.y
                            player.targeting_x = targeting_x
                            player.targeting_y = targeting_y
                            
                            # Find visible monsters
                            visible_monsters = []
                            for entity in entities:
                                if (entity.entity_type == EntityType.ENEMY and 
                                    entity.char != '%' and  # Not a corpse
                                    entity.fighter and  # Still alive
                                    game_map.visible[entity.y][entity.x]):  # Visible
                                    visible_monsters.append(entity)
                            
                            # Find closest visible monster
                            if visible_monsters:
                                closest_monster = None
                                closest_distance = float('inf')
                                
                                for monster in visible_monsters:
                                    dx = monster.x - player.x
                                    dy = monster.y - player.y
                                    distance = max(abs(dx), abs(dy))  # Chebyshev distance
                                    
                                    if distance < closest_distance:
                                        closest_distance = distance
                                        closest_monster = monster
                                
                                if closest_monster:
                                    targeting_x = closest_monster.x
                                    targeting_y = closest_monster.y
                                    player.targeting_x = targeting_x
                                    player.targeting_y = targeting_y
                            
                            message_log.add_message("Select a target and press T to fire, or ESC to cancel.", LIGHT_BLUE)
                            message_log.add_message("Use numpad to move cursor, or arrow keys to cycle through monsters.", LIGHT_BLUE)
                        else:
                            message_log.add_message("You need to equip arrows to use your bow!", YELLOW)
                    else:
                        message_log.add_message("You need to equip a ranged weapon first!", YELLOW)
                
                # Fire in targeting mode
                elif event.key == pygame.K_t and game_state == 'targeting':
                    # Make sure we're not targeting ourselves
                    if targeting_x == player.x and targeting_y == player.y:
                        message_log.add_message("You can't target yourself!", YELLOW)
                        continue
                    
                    # Check if target is in range
                    ranged_weapon = player.inventory.get_equipped_ranged_weapon()
                    if ranged_weapon:
                        # Calculate distance to target
                        dx = targeting_x - player.x
                        dy = targeting_y - player.y
                        distance = max(abs(dx), abs(dy))
                        
                        if distance > ranged_weapon.item.weapon_data.range:
                            message_log.add_message(f"Target is out of range! Maximum range is {ranged_weapon.item.weapon_data.range} tiles.", YELLOW)
                            continue
                        
                        # Check if target is visible
                        if not game_map.visible[targeting_y][targeting_x]:
                            message_log.add_message("You can't see that target!", YELLOW)
                            continue
                        
                        # Find the target entity
                        target = None
                        
                        # First try to find a living monster (non-corpse enemy)
                        for entity in entities:
                            if (entity.x == targeting_x and entity.y == targeting_y and 
                                entity.entity_type == EntityType.ENEMY and 
                                entity.char != '%' and entity.fighter):  # Not a corpse and still has fighter component
                                target = entity
                                break
                        
                        # If no living monster found, check for a corpse
                        if not target:
                            for entity in entities:
                                if (entity.x == targeting_x and entity.y == targeting_y and 
                                    entity.entity_type == EntityType.ENEMY):
                                    target = entity
                                    break
                        
                        if target:
                            # Use ammo
                            player.inventory.use_ammo()
                            
                            # Make sure target has a fighter component
                            if not target.fighter:
                                message_log.add_message(f"The {target.name} is already dead!", RED)
                                game_state = 'playing'
                                continue
                                
                            # Calculate dodge chance
                            dodge_chance = target.fighter.get_dodge_chance()
                            hit_roll = random.randint(1, 100)
                            
                            # Show the arrow animation
                            draw_arrow_path(player.x, player.y, targeting_x, targeting_y, camera_x, camera_y)
                            
                            if hit_roll > dodge_chance:
                                # Hit! Roll damage
                                damage_dice = ranged_weapon.item.damage_dice
                                damage = random.randint(1, damage_dice[1])
                                
                                # Add dexterity bonus for ranged attacks
                                damage += player.fighter.get_ranged_bonus()
                                
                                # Apply damage
                                old_hp = target.fighter.hp
                                target_name = target.name  # Store the name before it might change
                                result = target.fighter.take_damage(damage)
                                
                                # Get details about damage reduction if applicable
                                reduced_damage = damage
                                if result and result.startswith('damaged:'):
                                    reduced_damage = int(result.split(':', 1)[1])
                                
                                # Display hit message with damage and armor reduction
                                if reduced_damage < damage:
                                    hit_message = f"Your arrow hits the {target_name} for {damage} damage ({reduced_damage} after armor)!"
                                else:
                                    hit_message = f"Your arrow hits the {target_name} for {reduced_damage} damage!"
                                
                                message_log.add_message(hit_message, GREEN)
                                
                                # Check if target died
                                if target.fighter is None and old_hp > 0:
                                    message_log.add_message(f"The {target_name} dies!", LIGHT_BLUE)
                                    
                                    # Award XP to the player based on monster type
                                    xp_awarded = 0
                                    
                                    # Find the monster in the list by name
                                    for monster_key, monster_data in MONSTERS.items():
                                        if monster_data.name.lower() in target_name.lower():
                                            xp_awarded = monster_data.xp
                                            break
                                    
                                    # Fallback for monsters not in the list (should be rare)
                                    if xp_awarded == 0:
                                        if 'Orc' in target_name:
                                            xp_awarded = 50
                                        elif 'Troll' in target_name:
                                            xp_awarded = 100
                                        else:
                                            xp_awarded = 10  # Default XP
                                    
                                    player.fighter.xp += xp_awarded
                                    message_log.add_message(f"You gain {xp_awarded} XP!", LIGHT_BLUE)
                                    
                                    # Check for level up
                                    old_level = player.fighter.level
                                    # Check the level table for possible level up
                                    for level, xp_threshold, hit_dice, attack_bonus, attr_points in player.fighter.level_table:
                                        if level > player.fighter.level and player.fighter.xp >= xp_threshold:
                                            player.fighter.level_up(level, hit_dice, attack_bonus, attr_points, message_log)
                                            break
                            else:
                                message_log.add_message(
                                    f"Your arrow misses the {target.name}! (They dodged the attack)",
                                    RED
                                )
                        else:
                            message_log.add_message("There's no enemy at that location!", YELLOW)
                            # Still use up an arrow if firing at an empty spot
                            player.inventory.use_ammo()
                            
                            # Show arrow animation
                            draw_arrow_path(player.x, player.y, targeting_x, targeting_y, camera_x, camera_y)
                    
                    # Exit targeting mode after firing
                    game_state = 'playing'
                    
                    # Process monster turns after firing
                    for entity in entities:
                        if entity.ai and entity != player:
                            entity.ai.take_turn(player, game_map, message_log)
                    
                    # Check for game over after monsters take their turns
                    if player.fighter.hp <= 0:
                        game_state = 'dead'
                        message_log.add_message("You died!", RED)
                        game_over_time = pygame.time.get_ticks()  # Record time when game over happens
                
                # Quick Fire with 'f' key
                elif event.key == pygame.K_f and game_state == 'playing':
                    # Check if player has a ranged weapon equipped
                    ranged_weapon = player.inventory.get_equipped_ranged_weapon()
                    if ranged_weapon:
                        # Check if player has arrows equipped
                        if player.inventory.has_ammo_for_weapon():
                            # Find visible monsters
                            visible_monsters = []
                            for entity in entities:
                                if (entity.entity_type == EntityType.ENEMY and 
                                    entity.char != '%' and  # Not a corpse
                                    entity.fighter and  # Still alive
                                    game_map.visible[entity.y][entity.x]):  # Visible
                                    visible_monsters.append(entity)
                            
                            # Find closest visible monster
                            if visible_monsters:
                                closest_monster = None
                                closest_distance = float('inf')
                                
                                for monster in visible_monsters:
                                    dx = monster.x - player.x
                                    dy = monster.y - player.y
                                    distance = max(abs(dx), abs(dy))  # Chebyshev distance
                                    
                                    if distance < closest_distance:
                                        closest_distance = distance
                                        closest_monster = monster
                                
                                if closest_monster:
                                    # Check if target is in range
                                    if closest_distance > ranged_weapon.item.weapon_data.range:
                                        message_log.add_message(f"Closest monster ({closest_monster.name}) is out of range! Maximum range is {ranged_weapon.item.weapon_data.range} tiles.", YELLOW)
                                    else:
                                        # We have a target, fire!
                                        target = closest_monster
                                        targeting_x, targeting_y = target.x, target.y # For arrow animation
                                        
                                        # Use ammo
                                        player.inventory.use_ammo()
                                        
                                        # Calculate dodge chance
                                        dodge_chance = target.fighter.get_dodge_chance()
                                        hit_roll = random.randint(1, 100)
                                        
                                        # Show the arrow animation
                                        draw_arrow_path(player.x, player.y, targeting_x, targeting_y, camera_x, camera_y)
                                        
                                        if hit_roll > dodge_chance:
                                            # Hit! Roll damage
                                            damage_dice = ranged_weapon.item.damage_dice
                                            damage = random.randint(1, damage_dice[1])
                                            
                                            # Add dexterity bonus for ranged attacks
                                            damage += player.fighter.get_ranged_bonus()
                                            
                                            # Apply damage
                                            old_hp = target.fighter.hp
                                            target_name = target.name  # Store the name before it might change
                                            result = target.fighter.take_damage(damage)
                                            
                                            # Get details about damage reduction if applicable
                                            reduced_damage = damage
                                            if result and result.startswith('damaged:'):
                                                reduced_damage = int(result.split(':', 1)[1])
                                            
                                            # Display hit message with damage and armor reduction
                                            if reduced_damage < damage:
                                                hit_message = f"Your arrow hits the {target_name} for {damage} damage ({reduced_damage} after armor)!"
                                            else:
                                                hit_message = f"Your arrow hits the {target_name} for {reduced_damage} damage!"
                                            
                                            message_log.add_message(hit_message, GREEN)
                                            
                                            # Check if target died
                                            if target.fighter is None and old_hp > 0:
                                                message_log.add_message(f"The {target_name} dies!", LIGHT_BLUE)
                                                
                                                # Award XP to the player based on monster type
                                                xp_awarded = 0
                                                
                                                # Find the monster in the list by name
                                                for monster_key, monster_data in MONSTERS.items():
                                                    if monster_data.name.lower() in target_name.lower():
                                                        xp_awarded = monster_data.xp
                                                        break
                                                
                                                # Fallback for monsters not in the list (should be rare)
                                                if xp_awarded == 0:
                                                    if 'Orc' in target_name:
                                                        xp_awarded = 50
                                                    elif 'Troll' in target_name:
                                                        xp_awarded = 100
                                                    else:
                                                        xp_awarded = 10  # Default XP
                                                
                                                player.fighter.xp += xp_awarded
                                                message_log.add_message(f"You gain {xp_awarded} XP!", LIGHT_BLUE)
                                                
                                                # Check for level up
                                                old_level = player.fighter.level
                                                # Check the level table for possible level up
                                                for level, xp_threshold, hit_dice, attack_bonus, attr_points in player.fighter.level_table:
                                                    if level > player.fighter.level and player.fighter.xp >= xp_threshold:
                                                        player.fighter.level_up(level, hit_dice, attack_bonus, attr_points, message_log)
                                                        break
                                        else:
                                            message_log.add_message(
                                                f"Your arrow misses the {target.name}! (They dodged the attack)",
                                                RED
                                            )
                                            
                                        # Process monster turns after firing
                                        fov_recompute = True # Recompute FOV in case player moved
                                        for entity in entities:
                                            if entity.ai and entity != player:
                                                entity.ai.take_turn(player, game_map, message_log)
                                        
                                        # Check for game over after monsters take their turns
                                        if player.fighter.hp <= 0:
                                            game_state = 'dead'
                                            message_log.add_message("You died!", RED)
                                            game_over_time = pygame.time.get_ticks()  # Record time when game over happens
                                else:
                                    message_log.add_message("No monsters are close enough to Quick Fire!", YELLOW)
                            else:
                                message_log.add_message("No visible monsters to Quick Fire!", YELLOW)
                        else:
                            message_log.add_message("You need to equip arrows to use your bow!", YELLOW)
                    else:
                        message_log.add_message("You need to equip a ranged weapon first!", YELLOW)

                # Player movement
                if game_state == 'playing':
                    dx, dy = 0, 0
                    
                    # Regular arrow key movement (cardinal directions only)
                    if event.key == pygame.K_UP:
                        dy = -1
                    elif event.key == pygame.K_DOWN:
                        dy = 1
                    elif event.key == pygame.K_LEFT:
                        dx = -1
                    elif event.key == pygame.K_RIGHT:
                        dx = 1
                    
                    # Numpad movement (includes diagonals)
                    elif event.key == pygame.K_KP8:  # North
                        dy = -1
                    elif event.key == pygame.K_KP2:  # South
                        dy = 1
                    elif event.key == pygame.K_KP4:  # West
                        dx = -1
                    elif event.key == pygame.K_KP6:  # East
                        dx = 1
                    elif event.key == pygame.K_KP7:  # Northwest
                        dx, dy = -1, -1
                    elif event.key == pygame.K_KP9:  # Northeast
                        dx, dy = 1, -1
                    elif event.key == pygame.K_KP1:  # Southwest
                        dx, dy = -1, 1
                    elif event.key == pygame.K_KP3:  # Southeast
                        dx, dy = 1, 1
                    elif event.key == pygame.K_KP5:  # Wait (no movement)
                        message_log.add_message("You wait...", LIGHT_BLUE)
                        # Trigger enemy turns without player movement
                        for entity in entities:
                            if entity.ai and entity != player:
                                entity.ai.take_turn(player, game_map, message_log)
                        
                        # Check for game over after enemies take their turns
                        if player.fighter.hp <= 0:
                            game_state = 'dead'
                            message_log.add_message("You died!", RED)
                            game_over_time = pygame.time.get_ticks()  # Record time when game over happens
                        
                        fov_recompute = True  # Still recompute FOV for any enemy movement
                    
                    if dx != 0 or dy != 0:
                        # Process player movement
                        action_result = player.move(dx, dy, game_map, message_log)
                        
                        # Only add message if it's a string message (not just True)
                        if action_result and isinstance(action_result, str):
                            message_log.add_message(action_result)
                        
                        # Check for building interactions if player moved successfully
                        if action_result and isinstance(action_result, bool):
                            # Implement building interaction logic here
                            pass
                        
                        # Recalculate FOV after movement
                        fov_recompute = True
                        
                        # Enemy turns
                        for entity in entities:
                            if entity.ai and entity != player:
                                entity.ai.take_turn(player, game_map, message_log)
                        
                        # Check for game over
                        if player.fighter.hp <= 0:
                            game_state = 'dead'
                            message_log.add_message("You died!", RED)
                            game_over_time = pygame.time.get_ticks()  # Record time when game over happens
                        
                        # Pick up items feature
                        for entity in list(entities):  # Use a copy to avoid issues if we remove during iteration
                            if (entity.item and entity.x == player.x and entity.y == player.y and 
                                entity.entity_type == EntityType.ITEM):
                                
                                # Check if we're picking up an unpaid item from a shop
                                item_is_in_shop = False
                                for shop_entity in entities:
                                    if (shop_entity.entity_type == EntityType.ENEMY and 
                                        shop_entity.ai and hasattr(shop_entity.ai, 'shop_area')):
                                        # This is a shopkeeper, check if the item is in their shop
                                        x1, y1, x2, y2 = shop_entity.ai.shop_area
                                        if (x1 <= entity.x <= x2 and y1 <= entity.y <= y2):
                                            # The item is in a shop
                                            item_is_in_shop = True
                                            
                                            # Mark the item as unpaid and set its price if not already set
                                            if not entity.item.unpaid:
                                                entity.item.unpaid = True
                                                
                                                # Set a default price if needed based on item type
                                                if entity.item.price == 0:
                                                    if entity.item.item_type == ItemType.WEAPON or entity.item.item_type == ItemType.RANGED_WEAPON:
                                                        entity.item.price = 15
                                                    elif entity.item.item_type == ItemType.ARMOR:
                                                        entity.item.price = 25
                                                    elif entity.item.item_type == ItemType.CONSUMABLE:
                                                        entity.item.price = 20
                                                    else:
                                                        entity.item.price = 10
                                                
                                            # Make the shopkeeper move to block the exit
                                            shop_entity.ai.is_in_doorway = True
                                            shop_entity.x = shop_entity.ai.door_x
                                            shop_entity.y = shop_entity.ai.door_y
                                            
                                            # Add message about the shopkeeper's reaction
                                            message_log.add_message(f"The {shop_entity.name} moves to block the exit.", LIGHT_BLUE)
                                            break
                                
                                # Store item information for auto-equip
                                item_name = entity.name
                                
                                # Add item to inventory
                                if player.inventory.add_item(entity, message_log):
                                    entities.remove(entity)
                                    
                                    # Auto-equip functionality (only for non-shop items or paid items)
                                    if entity.item.equippable and not entity.item.unpaid:
                                        # Get the appropriate equipment slot for this item
                                        slot = entity.item.get_slot()
                                        if slot is not None:
                                            # Check if the slot is empty
                                            if player.inventory.get_equipped_item(slot) is None:
                                                # Find the item in the inventory
                                                for inv_item in player.inventory.items:
                                                    if inv_item.name == item_name:
                                                        # Auto-equip the item
                                                        player.inventory.equip_item(inv_item, slot, message_log, entities)
                                                        break

                # Stair movement keys
                if event.key == pygame.K_LESS and game_state == 'playing':
                    # Check if player is on up stairs
                    if (hasattr(game_map, 'up_stairs_position') and 
                        game_map.up_stairs_position and 
                        player.x == game_map.up_stairs_position[0] and 
                        player.y == game_map.up_stairs_position[1]):
                        # Player is on up stairs, try to go up
                        if game_world.go_up_stairs(player):
                            # Get the updated map and entities after level change
                            game_map, level_entities = game_world.get_current_level()
                            entities = [player] + level_entities
                            game_map.entities = entities
                            message_log.add_message("You climb up the stairs.", LIGHT_BLUE)
                            # Adjust FOV radius based on the new level
                            fov_radius = 20 if game_world.current_level == 0 else 10
                            fov_recompute = True
                        else:
                            message_log.add_message("You can't go up here.", YELLOW)
                    else:
                        message_log.add_message("There are no stairs up here.", YELLOW)
                
                elif event.key == pygame.K_GREATER and game_state == 'playing':
                    # Check if player is on down stairs
                    if (hasattr(game_map, 'down_stairs_position') and 
                        game_map.down_stairs_position and 
                        player.x == game_map.down_stairs_position[0] and 
                        player.y == game_map.down_stairs_position[1]):
                        # Player is on down stairs, try to go down
                        if game_world.go_down_stairs(player):
                            # Get the updated map and entities after level change
                            game_map, level_entities = game_world.get_current_level()
                            entities = [player] + level_entities
                            game_map.entities = entities
                            message_log.add_message("You descend deeper into the dungeon.", LIGHT_BLUE)
                            # Adjust FOV radius based on the new level
                            fov_radius = 20 if game_world.current_level == 0 else 10
                            fov_recompute = True
                        else:
                            message_log.add_message("You can't go down here.", YELLOW)
                    else:
                        message_log.add_message("There are no stairs down here.", YELLOW)
                
                # Add new handler for period with shift
                elif event.key == pygame.K_PERIOD and pygame.key.get_mods() & pygame.KMOD_SHIFT and game_state == 'playing':
                    # Check if player is on down stairs
                    if (hasattr(game_map, 'down_stairs_position') and 
                        game_map.down_stairs_position and 
                        player.x == game_map.down_stairs_position[0] and 
                        player.y == game_map.down_stairs_position[1]):
                        # Player is on down stairs, try to go down
                        if game_world.go_down_stairs(player):
                            # Get the updated map and entities after level change
                            game_map, level_entities = game_world.get_current_level()
                            entities = [player] + level_entities
                            game_map.entities = entities
                            message_log.add_message("You descend deeper into the dungeon.", LIGHT_BLUE)
                            # Adjust FOV radius based on the new level
                            fov_radius = 20 if game_world.current_level == 0 else 10
                            fov_recompute = True
                        else:
                            message_log.add_message("You can't go down here.", YELLOW)
                    else:
                        message_log.add_message("There are no stairs down here.", YELLOW)
                
                # Add new handler for comma with shift
                elif event.key == pygame.K_COMMA and pygame.key.get_mods() & pygame.KMOD_SHIFT and game_state == 'playing':
                    # Check if player is on up stairs
                    if (hasattr(game_map, 'up_stairs_position') and 
                        game_map.up_stairs_position and 
                        player.x == game_map.up_stairs_position[0] and 
                        player.y == game_map.up_stairs_position[1]):
                        # Player is on up stairs, try to go up
                        if game_world.go_up_stairs(player):
                            # Get the updated map and entities after level change
                            game_map, level_entities = game_world.get_current_level()
                            entities = [player] + level_entities
                            game_map.entities = entities
                            message_log.add_message("You climb up the stairs.", LIGHT_BLUE)
                            # Adjust FOV radius based on the new level
                            fov_radius = 20 if game_world.current_level == 0 else 10
                            fov_recompute = True
                        else:
                            message_log.add_message("You can't go up here.", YELLOW)
                    else:
                        message_log.add_message("There are no stairs up here.", YELLOW)
                
                # Targeting mode movement
                elif game_state == 'targeting':
                    dx, dy = 0, 0
                    
                    # Arrow keys cycle through visible monsters
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                        # Find all visible monsters
                        visible_monsters = []
                        for entity in entities:
                            if (entity.entity_type == EntityType.ENEMY and 
                                entity.char != '%' and  # Not a corpse
                                entity.fighter and  # Still alive
                                game_map.visible[entity.y][entity.x]):  # Visible
                                visible_monsters.append(entity)
                        
                        if visible_monsters:
                            # Sort monsters by position (left to right, top to bottom)
                            sorted_monsters = sorted(visible_monsters, key=lambda e: (e.x, e.y))
                            
                            # Find the current target in the sorted list
                            current_index = -1
                            for i, monster in enumerate(sorted_monsters):
                                if monster.x == targeting_x and monster.y == targeting_y:
                                    current_index = i
                                    break
                            
                            # Select the next monster
                            next_index = (current_index + 1) % len(sorted_monsters)
                            targeting_x = sorted_monsters[next_index].x
                            targeting_y = sorted_monsters[next_index].y
                            
                            # Adjust camera if needed
                            if targeting_x < camera_x + 2:
                                camera_x = max(0, targeting_x - 2)
                            elif targeting_x >= camera_x + view_width - 2:
                                camera_x = min(MAP_WIDTH - view_width, targeting_x - view_width + 4)
                                
                            if targeting_y < camera_y + 2:
                                camera_y = max(0, targeting_y - 2)
                            elif targeting_y >= camera_y + view_height - 2:
                                camera_y = min(MAP_HEIGHT - view_height, targeting_y - view_height + 4)
                    
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                        # Find all visible monsters
                        visible_monsters = []
                        for entity in entities:
                            if (entity.entity_type == EntityType.ENEMY and 
                                entity.char != '%' and  # Not a corpse
                                entity.fighter and  # Still alive
                                game_map.visible[entity.y][entity.x]):  # Visible
                                visible_monsters.append(entity)
                        
                        if visible_monsters:
                            # Sort monsters by position (left to right, top to bottom)
                            sorted_monsters = sorted(visible_monsters, key=lambda e: (e.x, e.y))
                            
                            # Find the current target in the sorted list
                            current_index = -1
                            for i, monster in enumerate(sorted_monsters):
                                if monster.x == targeting_x and monster.y == targeting_y:
                                    current_index = i
                                    break
                            
                            # Select the previous monster
                            prev_index = (current_index - 1) % len(sorted_monsters)
                            targeting_x = sorted_monsters[prev_index].x
                            targeting_y = sorted_monsters[prev_index].y
                            
                            # Adjust camera if needed
                            if targeting_x < camera_x + 2:
                                camera_x = max(0, targeting_x - 2)
                            elif targeting_x >= camera_x + view_width - 2:
                                camera_x = min(MAP_WIDTH - view_width, targeting_x - view_width + 4)
                                
                            if targeting_y < camera_y + 2:
                                camera_y = max(0, targeting_y - 2)
                            elif targeting_y >= camera_y + view_height - 2:
                                camera_y = min(MAP_HEIGHT - view_height, targeting_y - view_height + 4)
                    
                    # Numpad movement (includes diagonals) for precise targeting
                    elif event.key == pygame.K_KP8:  # North
                        dy = -1
                    elif event.key == pygame.K_KP2:  # South
                        dy = 1
                    elif event.key == pygame.K_KP4:  # West
                        dx = -1
                    elif event.key == pygame.K_KP6:  # East
                        dx = 1
                    elif event.key == pygame.K_KP7:  # Northwest
                        dx, dy = -1, -1
                    elif event.key == pygame.K_KP9:  # Northeast
                        dx, dy = 1, -1
                    elif event.key == pygame.K_KP1:  # Southwest
                        dx, dy = -1, 1
                    elif event.key == pygame.K_KP3:  # Southeast
                        dx, dy = 1, 1
                    
                    if dx != 0 or dy != 0:
                        # Move the targeting cursor (only for numpad keys)
                        new_x = targeting_x + dx
                        new_y = targeting_y + dy
                        
                        # Check if the new position is within map bounds
                        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                            targeting_x = new_x
                            targeting_y = new_y
                            
                            # Adjust camera if needed
                            if targeting_x < camera_x + 2:
                                camera_x = max(0, targeting_x - 2)
                            elif targeting_x >= camera_x + view_width - 2:
                                camera_x = min(MAP_WIDTH - view_width, targeting_x - view_width + 4)
                                
                            if targeting_y < camera_y + 2:
                                camera_y = max(0, targeting_y - 2)
                            elif targeting_y >= camera_y + view_height - 2:
                                camera_y = min(MAP_HEIGHT - view_height, targeting_y - view_height + 4)
                
                # Character sheet key handling
                if event.key == pygame.K_c and game_state == 'playing':
                    # Open character sheet to distribute attribute points
                    if player.fighter.attr_points > 0:
                        # Enter attribute distribution mode
                        game_state = 'character_sheet'
                        message_log.add_message(f"You have {player.fighter.attr_points} attribute points to distribute.", YELLOW)
                    else:
                        message_log.add_message("You don't have any attribute points to distribute.", YELLOW)
                
                # Handle character sheet controls
                if game_state == 'character_sheet':
                    if event.key == pygame.K_ESCAPE:
                        # Exit character sheet mode
                        game_state = 'playing'
                    elif event.key == pygame.K_UP:
                        # Move selection up
                        selected_attribute = (selected_attribute - 1) % len(attributes)
                    elif event.key == pygame.K_DOWN:
                        # Move selection down
                        selected_attribute = (selected_attribute + 1) % len(attributes)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Increase the selected attribute
                        if player.fighter.attr_points > 0:
                            # Get current attribute name
                            attr = attributes[selected_attribute]
                            # Increase attribute
                            if player.fighter.increase_attribute(attr):
                                message_log.add_message(f"You increased your {attribute_names[selected_attribute]} to {getattr(player.fighter, attr)}.", GREEN)
                            else:
                                message_log.add_message("You don't have enough attribute points.", RED)
                
                # Item usage (healing potion)
                if event.key == pygame.K_h and game_state == 'playing':
                    # First try to find a healing potion in inventory
                    healing_potion = player.inventory.find_item_by_type(ItemType.CONSUMABLE)
                    if healing_potion and healing_potion.item and healing_potion.item.use_function:
                        # Found a potion, use it
                        healing_potion.item.use(player, message_log, entities)
                
                # Toggle inventory screen
                if event.key == pygame.K_i:
                    if game_state == 'playing':
                        game_state = 'inventory'
                        inventory_index = 0  # Reset selection to first item
                    else:
                        game_state = 'playing'
                
                # Handle inventory controls
                if game_state == 'inventory':
                    # Switch between inventory and equipment
                    if event.key == pygame.K_LEFT:
                        inventory_mode = 'equipment'
                    elif event.key == pygame.K_RIGHT:
                        inventory_mode = 'items'
                    
                    # Navigate inventory based on current mode
                    if inventory_mode == 'items':
                        if event.key == pygame.K_UP:
                            inventory_index = max(0, inventory_index - 1)
                        elif event.key == pygame.K_DOWN:
                            inventory_index = min(len(player.inventory.items) - 1, inventory_index + 1) if player.inventory.items else 0
                    else:  # equipment mode
                        # Define the navigation order
                        equipment_order = [
                            EquipmentSlot.HEAD,
                            EquipmentSlot.LEFT_HAND,
                            EquipmentSlot.TORSO,
                            EquipmentSlot.RIGHT_HAND,
                            EquipmentSlot.LEGS,
                            EquipmentSlot.FEET
                        ]
                        
                        try:
                            current_index = equipment_order.index(selected_equipment_slot)
                        except ValueError:
                            # If current slot isn't in the order (shouldn't happen, but safety check)
                            current_index = 0
                            selected_equipment_slot = equipment_order[0]
                            
                        if event.key == pygame.K_UP:
                            # Move up in the defined order
                            new_index = (current_index - 1) % len(equipment_order)
                            selected_equipment_slot = equipment_order[new_index]
                        elif event.key == pygame.K_DOWN:
                            # Move down in the defined order
                            new_index = (current_index + 1) % len(equipment_order)
                            selected_equipment_slot = equipment_order[new_index]
                    
                    # Use/equip/unequip item
                    if event.key == pygame.K_RETURN:
                        if inventory_mode == 'items':
                            # Use/equip item from inventory
                            if player.inventory.items and 0 <= inventory_index < len(player.inventory.items):
                                selected_item = player.inventory.items[inventory_index]
                                if selected_item.item:
                                    selected_item.item.use(player, message_log, entities)
                        else:  # equipment mode
                            # Unequip item from equipment slot
                            equipped_item = player.inventory.get_equipped_item(selected_equipment_slot)
                            if equipped_item:
                                player.inventory.unequip_item(selected_equipment_slot, message_log, entities)
                    
                    # Drop item
                    if event.key == pygame.K_d:
                        if inventory_mode == 'items':
                            # Drop item from inventory
                            if player.inventory.items and 0 <= inventory_index < len(player.inventory.items):
                                selected_item = player.inventory.items[inventory_index]
                                if player.inventory.remove_item(selected_item):
                                    # Check if an item is already on the ground
                                    item_at_position = False
                                    for entity in entities:
                                        if (entity.entity_type == EntityType.ITEM and 
                                            entity.x == player.x and entity.y == player.y):
                                            item_at_position = True
                                            break
                                    
                                    if item_at_position:
                                        message_log.add_message(f"There's already an item on the ground here.", RED)
                                        player.inventory.add_item(selected_item, message_log)
                                    else:
                                        # Place item at player's feet
                                        selected_item.x = player.x
                                        selected_item.y = player.y
                                        message_log.add_message(f"You dropped the {selected_item.name}.", LIGHT_BLUE)
                                        entities.append(selected_item)
                                        # Adjust inventory index if needed
                                        if inventory_index >= len(player.inventory.items) and inventory_index > 0:
                                            inventory_index -= 1
                    
                    # Buy unpaid items from inventory
                    if event.key == pygame.K_b and game_state == 'playing':
                        # Buy unpaid items from shop
                        if player.inventory.has_unpaid_items():
                            if player.inventory.pay_for_items(message_log):
                                # Find all shopkeepers and make them move
                                for entity in entities:
                                    if (entity.entity_type == EntityType.ENEMY and 
                                        entity.ai and 
                                        hasattr(entity.ai, 'shop_area')):
                                        
                                        # Get shop boundaries
                                        x1, y1, x2, y2 = entity.ai.shop_area
                                        door_x, door_y = entity.ai.door_x, entity.ai.door_y
                                        
                                        # Calculate center of shop
                                        center_x = (x1 + x2) // 2
                                        center_y = (y1 + y2) // 2
                                        
                                        # Calculate vector from door to center of shop
                                        vector_x = center_x - door_x
                                        vector_y = center_y - door_y
                                        
                                        # Normalize to get direction
                                        dir_x = 1 if vector_x > 0 else (-1 if vector_x < 0 else 0)
                                        dir_y = 1 if vector_y > 0 else (-1 if vector_y < 0 else 0)
                                        
                                        # Calculate new position (try to move one step toward center)
                                        new_x = door_x + dir_x
                                        new_y = door_y + dir_y
                                        
                                        # Make sure it's inside the shop
                                        new_x = max(x1, min(x2, new_x))
                                        new_y = max(y1, min(y2, new_y))
                                        
                                        # FORCE MOVE the shopkeeper to this position
                                        entity.force_move(new_x, new_y)
                                        message_log.add_message(f"The {entity.name} steps aside.", LIGHT_BLUE)
                            else:
                                message_log.add_message("You don't have enough silver.", RED)
                        else:
                            message_log.add_message("You don't have any unpaid items to buy.", YELLOW)
                
                # Add handler for selling items on the floor
                elif event.key == pygame.K_s and game_state == 'playing':
                    # Sell items on the floor
                    in_shop = False
                    shopkeeper = None
                    shop_items = []
                    
                    # First identify if we're in a shop by finding a shopkeeper
                    for entity in entities:
                        if (entity.entity_type == EntityType.ENEMY and 
                            entity.ai and 
                            hasattr(entity.ai, 'shop_area')):
                            # Found a shopkeeper, check if player is in the shop
                            x1, y1, x2, y2 = entity.ai.shop_area
                            if (x1 <= player.x <= x2 and y1 <= player.y <= y2):
                                in_shop = True
                                shopkeeper = entity
                                break
                    
                    if in_shop and shopkeeper:
                        # Find items on the floor of this shop
                        x1, y1, x2, y2 = shopkeeper.ai.shop_area
                        for entity in list(entities):  # Use a copy for safe removal
                            if (entity.entity_type == EntityType.ITEM and 
                                x1 <= entity.x <= x2 and 
                                y1 <= entity.y <= y2 and
                                entity.x == player.x and
                                entity.y == player.y):
                                # Found an item on the floor under the player
                                shop_items.append(entity)
                        
                        if shop_items:
                            total_value = 0
                            
                            # Calculate the value of the items (half of purchase price)
                            for item in shop_items:
                                if item.item and item.item.price:
                                    item_value = item.item.price // 2
                                else:
                                    # Default value for items without a price
                                    item_value = 5
                                
                                total_value += item_value
                                
                                # Remove item from game
                                entities.remove(item)
                            
                            # Give player silver for the items
                            player.silver_pieces += total_value
                            message_log.add_message(f"You sell the items for {total_value} silver.", LIGHT_BLUE)
                            
                            # Tell shopkeeper to step aside since transaction is complete
                            if hasattr(shopkeeper.ai, 'shop_area'):
                                # Get shop boundaries
                                x1, y1, x2, y2 = shopkeeper.ai.shop_area
                                door_x, door_y = shopkeeper.ai.door_x, shopkeeper.ai.door_y
                                
                                # Calculate center of shop
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                
                                # Calculate vector from door to center of shop
                                vector_x = center_x - door_x
                                vector_y = center_y - door_y
                                
                                # Normalize to get direction
                                dir_x = 1 if vector_x > 0 else (-1 if vector_x < 0 else 0)
                                dir_y = 1 if vector_y > 0 else (-1 if vector_y < 0 else 0)
                                
                                # Calculate new position (try to move one step toward center)
                                new_x = door_x + dir_x
                                new_y = door_y + dir_y
                                
                                # Make sure it's inside the shop
                                new_x = max(x1, min(x2, new_x))
                                new_y = max(y1, min(y2, new_y))
                                
                                # FORCE MOVE the shopkeeper to this position
                                shopkeeper.force_move(new_x, new_y)
                                message_log.add_message(f"The {shopkeeper.name} steps aside.", LIGHT_BLUE)
                        else:
                            message_log.add_message("There are no items here to sell.", YELLOW)
                    else:
                        message_log.add_message("You're not in a shop or there's no shopkeeper nearby.", YELLOW)
            
            # Handle different game states
            if game_state == 'playing':
                if event.type == pygame.KEYDOWN:
                    pass  # No additional handling needed for 'playing' state here
            
            elif game_state == 'targeting':
                if event.type == pygame.KEYDOWN:
                    pass  # No additional handling needed for 'targeting' state here
            
            elif game_state == 'inventory':
                if event.type == pygame.KEYDOWN:
                    pass  # No additional handling needed for 'inventory' state here
            
            elif game_state == 'character_sheet':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Exit character sheet mode
                        game_state = 'playing'
                    elif event.key == pygame.K_UP:
                        # Move selection up
                        selected_attribute = (selected_attribute - 1) % len(attributes)
                    elif event.key == pygame.K_DOWN:
                        # Move selection down
                        selected_attribute = (selected_attribute + 1) % len(attributes)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Increase the selected attribute
                        if player.fighter.attr_points > 0:
                            # Get current attribute name
                            attr = attributes[selected_attribute]
                            # Increase attribute
                            if player.fighter.increase_attribute(attr):
                                message_log.add_message(f"You increased your {attribute_names[selected_attribute]} to {getattr(player.fighter, attr)}.", GREEN)
                            else:
                                message_log.add_message("You don't have enough attribute points.", RED)
        
        # Update game state
        if fov_recompute:
            # Adjust FOV radius based on current level
            fov_radius = 20 if game_world.current_level == 0 else 10  # Double FOV in town
            calculate_fov(game_map, player.x, player.y, fov_radius)
            fov_recompute = False
        
        # Auto-explore logic
        if auto_explore and game_state == 'playing':
            # Check for enemies in FOV before moving
            found_enemy = False
            for entity in entities:
                if (entity.entity_type == EntityType.ENEMY and 
                    entity.char != '%' and  # Not a corpse
                    entity.fighter and  # Still alive
                    game_map.visible[entity.y][entity.x]):  # Visible
                    found_enemy = True
                    auto_explore = False
                    message_log.add_message("Stopped auto-exploration: Monster spotted!", YELLOW)
                    break
            
            if not found_enemy:
                # Check for visible silver or potions first
                visible_items = []
                for entity in entities:
                    if (entity.entity_type == EntityType.ITEM and 
                        game_map.visible[entity.y][entity.x] and
                        (entity.name == "Silver" or 
                            (entity.item and entity.item.item_type == ItemType.CONSUMABLE and player.inventory.has_space()))):
                        visible_items.append(entity)
                
                # If we found visible valuable items, path to the closest one
                if visible_items and (not auto_explore_path or auto_explore_target is None or auto_explore_target[2] != "item"):
                    closest_item = None
                    closest_distance = float('inf')
                    
                    for item in visible_items:
                        distance = abs(item.x - player.x) + abs(item.y - player.y)
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_item = item
                    
                    if closest_item:
                        # Get path to the closest item
                        auto_explore_target = (closest_item.x, closest_item.y, "item")
                        auto_explore_path = game_map.get_path(player.x, player.y, closest_item.x, closest_item.y)
                        if auto_explore_path:
                            message_log.add_message(f"You spot a {closest_item.name}!", LIGHT_BLUE)
                
                # If we don't have a path or have reached the target, find a new target
                if not auto_explore_path or auto_explore_target is None:
                    # Find unexplored tiles adjacent to explored tiles
                    frontier_tiles = game_map.get_unexplored_tiles(explored_only=True)
                    
                    # If no frontier tiles, try any unexplored tile
                    if not frontier_tiles:
                        frontier_tiles = game_map.get_unexplored_tiles(explored_only=False)
                    
                    # If still no unexplored tiles, stop auto-explore
                    if not frontier_tiles:
                        auto_explore = False
                        message_log.add_message("Stopped auto-exploration: No unexplored tiles left!", LIGHT_BLUE)
                    else:
                        # Find closest unexplored tile
                        closest_tile = None
                        closest_distance = float('inf')
                        
                        for tile_x, tile_y in frontier_tiles:
                            distance = abs(tile_x - player.x) + abs(tile_y - player.y)
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_tile = (tile_x, tile_y)
                        
                        if closest_tile:
                            # Get path to the closest unexplored tile
                            auto_explore_target = (closest_tile[0], closest_tile[1], "explore")
                            auto_explore_path = game_map.get_path(player.x, player.y, closest_tile[0], closest_tile[1])
                
                # If we have a path, follow it
                if auto_explore_path:
                    next_step = auto_explore_path[0]
                    dx = next_step[0] - player.x
                    dy = next_step[1] - player.y
                    
                    # Check for pickup items before moving
                    item_picked_up = False
                    for entity in list(entities):
                        if (entity.item and entity.x == player.x and entity.y == player.y and 
                            entity.entity_type == EntityType.ITEM):
                            # Check if it's silver or a potion
                            if entity.name == "Silver" or (entity.item.item_type == ItemType.CONSUMABLE and player.inventory.has_space()):
                                # Store item information for auto-equip
                                item_name = entity.name
                                
                                # Add item to inventory
                                if player.inventory.add_item(entity, message_log):
                                    entities.remove(entity)
                                    item_picked_up = True
                                    
                                    # Auto-equip functionality
                                    if entity.item.equippable:
                                        # Get the appropriate equipment slot for this item
                                        slot = entity.item.get_slot()
                                        if slot is not None:
                                            # Check if the slot is empty
                                            if player.inventory.get_equipped_item(slot) is None:
                                                # Find the item in the inventory
                                                for inv_item in player.inventory.items:
                                                    if inv_item.name == item_name:
                                                        # Auto-equip the item
                                                        player.inventory.equip_item(inv_item, slot, message_log, entities)
                                                        break
                    
                    if not item_picked_up:
                        # Move or attack
                        action_result = player.move(dx, dy, game_map, message_log)
                        
                        # Only add message if it's a string message (not just True)
                        if action_result and isinstance(action_result, str):
                            message_log.add_message(action_result)
                        
                        # Remove the step we just took
                        auto_explore_path.pop(0)
                        
                        # If we attacked something, stop auto-explore
                        if action_result and isinstance(action_result, str) and "attack" in action_result:
                            auto_explore = False
                            message_log.add_message("Stopped auto-exploration: Combat initiated!", YELLOW)
                        
                        # Recalculate FOV after movement
                        fov_recompute = True
                        
                        # Enemy turns
                        for entity in entities:
                            if entity.ai and entity != player:
                                entity.ai.take_turn(player, game_map, message_log)
                        
                        # Check for game over
                        if player.fighter.hp <= 0:
                            game_state = 'dead'
                            auto_explore = False
                            message_log.add_message("You died!", RED)
                            game_over_time = pygame.time.get_ticks()  # Record time when game over happens
                            player_died = True
        
        # Save entities to current level before drawing
        game_world.update_entities(entities)
        
        # Adjust camera to center on player
        camera_x = max(0, min(MAP_WIDTH - view_width, player.x - view_width // 2))
        camera_y = max(0, min(MAP_HEIGHT - view_height, player.y - view_height // 2))
        
        # Draw everything
        screen.fill(UI_BACKGROUND)
        
        # Use the new UI system to draw the game UI
        draw_game_ui(player, game_world, game_map, message_log, camera_x, camera_y, game_state, 
                     inventory_index, inventory_mode, selected_equipment_slot)
        
        # If the game is over, draw game over message
        if game_state == 'dead':
            font = ThemeManager.FONT_HEADING
            text = font.render('GAME OVER', True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)
            
            # Check if 3 seconds have passed since game over
            if game_over_time and pygame.time.get_ticks() - game_over_time >= 3000:
                running = False
                should_return_to_title = True  # Return to title screen instead of exiting
                player_died = True  # Set the player_died flag
        
        # Update the display
        pygame.display.flip()
    
    # Return to the main menu or exit the game
    if not should_return_to_title:
        # Quit Pygame
        pygame.quit()
        sys.exit()
    
    # Return whether the player died, so the main function can reset the player
    return player_died

# Add to the drawing code
def draw_character_sheet(player, selected_attribute, attributes, attribute_names):
    """Draw the character sheet screen for attribute distribution"""
    # Clear the screen
    screen.fill(BLACK)
    
    # Initialize fonts
    large_font = pygame.font.SysFont('Arial', 24)
    font = pygame.font.SysFont('Arial', 16)
    small_font = pygame.font.SysFont('Arial', 12)
    
    # Draw the title
    title_text = large_font.render("CHARACTER SHEET", True, YELLOW)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 20))
    
    # Draw available points
    points_text = font.render(f"Available Points: {player.fighter.attr_points}", True, WHITE)
    screen.blit(points_text, (SCREEN_WIDTH // 2 - points_text.get_width() // 2, 60))
    
    # Draw attributes
    y_pos = 100
    for i, (attr, name) in enumerate(zip(attributes, attribute_names)):
        # Highlight selected attribute
        color = YELLOW if i == selected_attribute else WHITE
        
        # Get attribute value
        value = getattr(player.fighter, attr)
        
        # Draw attribute name and value
        attr_text = font.render(f"{name}: {value}", True, color)
        screen.blit(attr_text, (SCREEN_WIDTH // 2 - attr_text.get_width() // 2, y_pos))
        
        # Show effect of attribute if applicable
        effect_text = None
        if attr == 'str':
            effect_text = f"Melee Damage Bonus: +{player.fighter.get_damage_bonus()}"
        elif attr == 'dex':
            effect_text = f"Dodge Chance: {player.fighter.get_dodge_chance()}%"
        elif attr == 'con':
            effect_text = f"HP Bonus: +{player.fighter.get_hp_bonus()} per level"
        
        if effect_text:
            bonus_text = small_font.render(effect_text, True, LIGHT_BLUE)
            screen.blit(bonus_text, (SCREEN_WIDTH // 2 - bonus_text.get_width() // 2, y_pos + 25))
        
        y_pos += 50
    
    # Draw instructions
    instructions = [
        "Use UP/DOWN arrows to select an attribute",
        "Press ENTER to increase the selected attribute",
        "Press ESC to exit character sheet"
    ]
    
    y_pos = SCREEN_HEIGHT - 100
    for instruction in instructions:
        instr_text = small_font.render(instruction, True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, y_pos))
        y_pos += 25
    
    # Update the display
    pygame.display.flip()

if __name__ == "__main__":
    main()
