import pygame
from config import (
    BLACK, WHITE, GRAY, RED, GREEN, LIGHT_BLUE, YELLOW,
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, LEFT_PANEL_WIDTH, 
    MESSAGE_LOG_HEIGHT, screen, EntityType, ItemType
)
from ui.rendering import draw_text
from data.items import ITEM_PRICES, create_item

def render_shop_window(title, message=None):
    """Render the base shop window"""
    # Window dimensions
    window_width = LEFT_PANEL_WIDTH * TILE_SIZE - 100
    window_height = (SCREEN_HEIGHT - MESSAGE_LOG_HEIGHT * TILE_SIZE) - 100
    window_x = (LEFT_PANEL_WIDTH * TILE_SIZE - window_width) // 2
    window_y = 50
    
    # Draw window background
    pygame.draw.rect(screen, BLACK, (window_x, window_y, window_width, window_height))
    pygame.draw.rect(screen, WHITE, (window_x, window_y, window_width, window_height), 2)
    
    # Draw title
    font = pygame.font.SysFont('Arial', 28)
    title_text = font.render(title, True, YELLOW)
    title_x = window_x + (window_width - title_text.get_width()) // 2
    screen.blit(title_text, (title_x, window_y + 15))
    
    # Draw horizontal line below title
    pygame.draw.line(screen, WHITE, (window_x + 20, window_y + 50), (window_x + window_width - 20, window_y + 50))
    
    # Draw message if provided
    if message:
        message_font = pygame.font.SysFont('Arial', 18)
        message_text = message_font.render(message, True, LIGHT_BLUE)
        message_x = window_x + (window_width - message_text.get_width()) // 2
        screen.blit(message_text, (message_x, window_y + 60))
    
    return window_x, window_y, window_width, window_height

def weaponsmith_interface(player, message_log, entities):
    """Shop interface for the weaponsmith to buy weapons"""
    # Available items at the weaponsmith
    available_items = [
        {"name": "dagger", "type": ItemType.WEAPON, "price": ITEM_PRICES["dagger"]},
        {"name": "shortsword", "type": ItemType.WEAPON, "price": ITEM_PRICES["shortsword"]},
        {"name": "longsword", "type": ItemType.WEAPON, "price": ITEM_PRICES["longsword"]},
        {"name": "battleaxe", "type": ItemType.WEAPON, "price": ITEM_PRICES["battleaxe"]},
        {"name": "shortbow", "type": ItemType.RANGED_WEAPON, "price": ITEM_PRICES["shortbow"]},
        {"name": "arrows", "type": ItemType.AMMO, "price": ITEM_PRICES["arrows"]}
    ]
    
    # Create window
    window_x, window_y, window_width, window_height = render_shop_window(
        "Weaponsmith", 
        "Buy weapons and ammunition"
    )
    
    # Draw player's current silver
    silver_text = f"Your Silver: {player.silver_pieces} sp"
    draw_text(silver_text, window_x + 20, window_y + 100, WHITE)
    
    # Draw shop items
    y_pos = window_y + 140
    for idx, item in enumerate(available_items):
        item_text = f"{idx + 1}. {item['name'].replace('_', ' ').title()} - {item['price']} silver"
        draw_text(item_text, window_x + 20, y_pos, WHITE)
        y_pos += 25
    
    # Draw instructions
    instructions = "Press number to buy item, [ESC] to leave"
    draw_text(instructions, window_x + 20, window_y + window_height - 60, LIGHT_BLUE)
    
    # Update display
    pygame.display.flip()
    
    # Handle input
    waiting_for_input = True
    result = None
    
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                    # Buying item
                    item_idx = event.key - pygame.K_1
                    if item_idx < len(available_items):
                        item = available_items[item_idx]
                        
                        # Check if player has enough silver
                        if player.silver_pieces >= item["price"]:
                            # Deduct silver
                            player.silver_pieces -= item["price"]
                            
                            # Create and add item to inventory
                            new_item = create_item(item["name"], player.x, player.y)
                            player.inventory.add_item(new_item, message_log)
                            
                            message_log.add_message(f"You purchased a {item['name'].replace('_', ' ')} for {item['price']} silver.", GREEN)
                        else:
                            message_log.add_message(f"You don't have enough silver to buy that item.", RED)
                        
                        waiting_for_input = False
                        result = 'buy'
                
                elif event.key == pygame.K_ESCAPE:
                    message_log.add_message("You leave the Weaponsmith's shop.", LIGHT_BLUE)
                    waiting_for_input = False
                    result = 'cancel'
    
    return result

def armorsmith_interface(player, message_log, entities):
    """Shop interface for the armorsmith to buy armor and shields"""
    # Available items at the armorsmith
    available_items = [
        {"name": "leather_armor", "type": ItemType.ARMOR, "price": ITEM_PRICES["leather_armor"]},
        {"name": "chainmail", "type": ItemType.ARMOR, "price": ITEM_PRICES["chainmail"]},
        {"name": "plate_armor", "type": ItemType.ARMOR, "price": ITEM_PRICES["plate_armor"]},
        {"name": "helmet", "type": ItemType.HELMET, "price": ITEM_PRICES["helmet"]},
        {"name": "boots", "type": ItemType.ARMOR, "price": ITEM_PRICES["boots"]},
        {"name": "gloves", "type": ItemType.ARMOR, "price": ITEM_PRICES["gloves"]},
        {"name": "shield", "type": ItemType.SHIELD, "price": ITEM_PRICES["shield"]}
    ]
    
    # Create window
    window_x, window_y, window_width, window_height = render_shop_window(
        "Armorsmith", 
        "Buy armor and protective equipment"
    )
    
    # Draw player's current silver
    silver_text = f"Your Silver: {player.silver_pieces} sp"
    draw_text(silver_text, window_x + 20, window_y + 100, WHITE)
    
    # Draw shop items
    y_pos = window_y + 140
    for idx, item in enumerate(available_items):
        item_text = f"{idx + 1}. {item['name'].replace('_', ' ').title()} - {item['price']} silver"
        draw_text(item_text, window_x + 20, y_pos, WHITE)
        y_pos += 25
    
    # Draw instructions
    instructions = "Press number to buy item, [ESC] to leave"
    draw_text(instructions, window_x + 20, window_y + window_height - 60, LIGHT_BLUE)
    
    # Update display
    pygame.display.flip()
    
    # Handle input
    waiting_for_input = True
    result = None
    
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                    # Buying item
                    item_idx = event.key - pygame.K_1
                    if item_idx < len(available_items):
                        item = available_items[item_idx]
                        
                        # Check if player has enough silver
                        if player.silver_pieces >= item["price"]:
                            # Deduct silver
                            player.silver_pieces -= item["price"]
                            
                            # Create and add item to inventory
                            new_item = create_item(item["name"], player.x, player.y)
                            player.inventory.add_item(new_item, message_log)
                            
                            message_log.add_message(f"You purchased a {item['name'].replace('_', ' ')} for {item['price']} silver.", GREEN)
                        else:
                            message_log.add_message(f"You don't have enough silver to buy that item.", RED)
                        
                        waiting_for_input = False
                        result = 'buy'
                
                elif event.key == pygame.K_ESCAPE:
                    message_log.add_message("You leave the Armorsmith's shop.", LIGHT_BLUE)
                    waiting_for_input = False
                    result = 'cancel'
    
    return result

def apothecary_interface(player, message_log, entities):
    """Shop interface for the apothecary to buy healing potions"""
    # Create window
    window_x, window_y, window_width, window_height = render_shop_window(
        "Apothecary", 
        "Buy healing potions and remedies"
    )
    
    # Draw player's current silver
    silver_text = f"Your Silver: {player.silver_pieces} sp"
    draw_text(silver_text, window_x + 20, window_y + 100, WHITE)
    
    # Draw shop items
    potion_price = ITEM_PRICES["healing_potion"]
    potion_text = f"1. Healing Potion - {potion_price} silver"
    draw_text(potion_text, window_x + 20, window_y + 140, WHITE)
    
    # Draw description
    description = "Restores health when consumed."
    draw_text(description, window_x + 40, window_y + 165, LIGHT_BLUE)
    
    # Draw instructions
    instructions = "Press [1] to buy a healing potion, [ESC] to leave"
    draw_text(instructions, window_x + 20, window_y + window_height - 60, LIGHT_BLUE)
    
    # Update display
    pygame.display.flip()
    
    # Handle input
    waiting_for_input = True
    result = None
    
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    # Buying healing potion
                    if player.silver_pieces >= potion_price:
                        # Deduct silver
                        player.silver_pieces -= potion_price
                        
                        # Create and add potion to inventory
                        potion = create_item("healing_potion", player.x, player.y)
                        player.inventory.add_item(potion, message_log)
                        
                        message_log.add_message(f"You purchased a healing potion for {potion_price} silver.", GREEN)
                    else:
                        message_log.add_message(f"You don't have enough silver to buy a healing potion.", RED)
                    
                    waiting_for_input = False
                    result = 'buy'
                
                elif event.key == pygame.K_ESCAPE:
                    message_log.add_message("You leave the Apothecary's shop.", LIGHT_BLUE)
                    waiting_for_input = False
                    result = 'cancel'
    
    return result 