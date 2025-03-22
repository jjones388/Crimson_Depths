import pygame
import sys
import random
from .config import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, LEFT_PANEL_WIDTH, MESSAGE_LOG_HEIGHT,
    INFO_PANEL_WIDTH, MAP_WIDTH, MAP_HEIGHT, BLACK, WHITE, RED, LIGHT_BLUE, YELLOW,
    screen, EntityType, EquipmentSlot, ItemType
)
from .map.map import Map
from .map.fov import calculate_fov
from .entities.entity import Entity
from .entities.components.fighter import Fighter
from .entities.components.ai import BasicMonster
from .entities.components.item import Item, heal_player
from .entities.inventory import Inventory
from .game.world import GameWorld
from .data.items import place_entities
from .ui.message_log import MessageLog
from .ui.rendering import (
    draw_borders, draw_map, draw_entities, draw_info_panel, 
    draw_message_log, draw_inventory
)
from .ui.title_screen import title_screen

def main():
    # Show the title screen first
    choice = title_screen()
    
    # Check the user's choice
    if choice != "new_game":
        # If the user didn't choose "New Game", exit
        # (Load Game and Options would have their own logic)
        return
    
    # Create the game world with multiple levels
    game_world = GameWorld(max_levels=20)
    
    # Create message log
    message_log = MessageLog()
    message_log.add_message("Welcome to Crimson Depths! Use arrow keys to move.", LIGHT_BLUE)
    message_log.add_message("Find the stairs (>) to descend deeper into the dungeon.", LIGHT_BLUE)
    message_log.add_message("Press I to open inventory.", LIGHT_BLUE)
    
    # Create inventory for player
    inventory_component = Inventory()
    
    # Create player with OSR-style stats
    fighter_component = Fighter(hp=8, ac=11, damage_dice=(1, 3))
    player = Entity(0, 0, '@', WHITE, EntityType.PLAYER, 'Player', blocks=True, 
                  fighter=fighter_component, inventory=inventory_component)
    
    # Initialize first level
    game_map, level_entities = game_world.get_current_level()
    
    # Place player in first room of first level
    player.x = game_map.rooms[0].center_x
    player.y = game_map.rooms[0].center_y
    
    # Add player to entities list
    entities = [player] + level_entities
    game_map.entities = entities
    
    # Camera offsets - adjusted for new layout
    view_width = LEFT_PANEL_WIDTH - 2
    view_height = (SCREEN_HEIGHT // TILE_SIZE) - MESSAGE_LOG_HEIGHT - 2
    camera_x = max(0, min(MAP_WIDTH - view_width, player.x - view_width // 2))
    camera_y = max(0, min(MAP_HEIGHT - view_height, player.y - view_height // 2))
    
    # Game state - add inventory state
    game_state = 'playing'  # Can be 'playing', 'inventory', or 'dead'
    game_over_time = None
    inventory_index = 0  # Currently selected inventory item
    inventory_mode = 'items'  # Can be 'items' or 'equipment'
    selected_equipment_slot = EquipmentSlot.RIGHT_HAND  # Currently selected equipment slot
    
    # FOV radius
    fov_radius = 10
    fov_recompute = True
    
    # Initial FOV calculation before game starts
    calculate_fov(game_map, player.x, player.y, fov_radius)
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    while running:
        # Limit the frame rate
        clock.tick(60)
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
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
                        fov_recompute = True  # Still recompute FOV for any enemy movement
                    
                    if dx != 0 or dy != 0:
                        # Move or attack
                        action_result = player.move(dx, dy, game_map, message_log)
                        
                        # Only add message if it's a string message (not just True)
                        if action_result and isinstance(action_result, str):
                            message_log.add_message(action_result)
                        
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
                                # Add item to inventory
                                if player.inventory.add_item(entity, message_log):
                                    entities.remove(entity)
                
                # Handle stairs movement
                if event.key == pygame.K_PERIOD and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # Go down stairs with ">" (Shift + Period)
                    if game_world.go_down_stairs(player):
                        game_map, level_entities = game_world.get_current_level()
                        entities = [player] + level_entities
                        game_map.entities = entities
                        message_log.add_message(f"You descend deeper into the dungeon to level {game_world.current_level}.", LIGHT_BLUE)
                        fov_recompute = True
                    else:
                        message_log.add_message("There are no stairs down here.", YELLOW)
                
                if event.key == pygame.K_COMMA and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # Go up stairs with "<" (Shift + Comma)
                    if game_world.go_up_stairs(player):
                        game_map, level_entities = game_world.get_current_level()
                        entities = [player] + level_entities
                        game_map.entities = entities
                        message_log.add_message(f"You climb up to level {game_world.current_level}.", LIGHT_BLUE)
                        fov_recompute = True
                    else:
                        message_log.add_message("There are no stairs up here.", YELLOW)
                
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
                        if event.key == pygame.K_UP:
                            # Navigate equipment slots
                            equipment_slots = list(EquipmentSlot)
                            current_index = equipment_slots.index(selected_equipment_slot)
                            selected_equipment_slot = equipment_slots[max(0, current_index - 1)]
                        elif event.key == pygame.K_DOWN:
                            # Navigate equipment slots
                            equipment_slots = list(EquipmentSlot)
                            current_index = equipment_slots.index(selected_equipment_slot)
                            selected_equipment_slot = equipment_slots[min(len(equipment_slots) - 1, current_index + 1)]
                    
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
        
        # Recompute FOV if needed
        if fov_recompute:
            calculate_fov(game_map, player.x, player.y, fov_radius)
            fov_recompute = False
        
        # Update camera position - adjusted for new layout
        view_width = LEFT_PANEL_WIDTH - 2
        view_height = (SCREEN_HEIGHT // TILE_SIZE) - MESSAGE_LOG_HEIGHT - 2
        camera_x = max(0, min(MAP_WIDTH - view_width, player.x - view_width // 2))
        camera_y = max(0, min(MAP_HEIGHT - view_height, player.y - view_height // 2))
        
        # Clear the screen
        screen.fill(BLACK)
        
        # Draw the map and entities
        draw_map(game_map, camera_x, camera_y)
        draw_entities(entities, game_map, camera_x, camera_y)
        
        # Save entities to current level before drawing
        game_world.update_entities(entities)
        
        # Draw UI elements
        draw_borders()
        draw_info_panel(player, game_world)
        draw_message_log(message_log)
        
        # Draw inventory screen if open
        if game_state == 'inventory':
            draw_inventory(player, inventory_index, inventory_mode, selected_equipment_slot)
        
        # If the game is over, draw game over message
        if game_state == 'dead':
            font = pygame.font.SysFont('Arial', 48)
            text = font.render('GAME OVER', True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)
            
            # Check if 3 seconds have passed since game over
            if game_over_time and pygame.time.get_ticks() - game_over_time >= 3000:
                running = False
        
        # Update the screen
        pygame.display.flip()
    
    # Quit Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
