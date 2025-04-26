import pygame
import sys
import random
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, YELLOW, LIGHT_BLUE, RED, 
    DEEP_CRIMSON, DARK_PURPLE, OBSIDIAN_BLACK, BURNISHED_GOLD, BLOOD_RED,
    UI_BACKGROUND, UI_TEXT_PRIMARY, UI_HIGHLIGHT, UI_BUTTON_NORMAL,
    UI_BUTTON_HOVER, UI_BUTTON_ACTIVE, screen
)
from ui.theme import ThemeManager

def draw_title_screen(selected_index, show_resume=False):
    """Draw the title screen with the given button selected"""
    # Fill screen with dark background
    screen.fill(UI_BACKGROUND)
    
    # Create a subtle dark gradient background
    for y in range(0, SCREEN_HEIGHT, 2):
        color_val = max(10, 35 - int(y / SCREEN_HEIGHT * 25))
        pygame.draw.line(screen, (color_val, color_val, color_val + 5), 
                        (0, y), (SCREEN_WIDTH, y))
    
    # Add animated particles effect
    current_time = pygame.time.get_ticks() / 1000.0
    for i in range(50):
        # Use time to create continuous movement
        x = (SCREEN_WIDTH * (0.2 + 0.6 * ((i * 0.037 + current_time * 0.1) % 1.0)))
        y = (SCREEN_HEIGHT * (0.1 + 0.7 * ((i * 0.053 + current_time * 0.05) % 1.0)))
        
        # Vary size and opacity based on position
        size = 2 + int(3 * math.sin(i * 0.1 + current_time))
        alpha = 100 + int(100 * math.sin(i * 0.2 + current_time * 0.7))
        
        # Choose particle color
        colors = [BLOOD_RED, DEEP_CRIMSON, BURNISHED_GOLD]
        color = colors[i % len(colors)]
        
        # Draw the particle
        particle_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*color[:3], alpha), (size//2, size//2), size//2)
        screen.blit(particle_surf, (x, y))
    
    # Game title with shadow effect
    title_text = "Crimson Depths"
    font_title = ThemeManager.FONT_HEADING
    
    # Draw shadow
    shadow_surf = font_title.render(title_text, True, DEEP_CRIMSON)
    shadow_x = (SCREEN_WIDTH - shadow_surf.get_width()) // 2 + 3
    screen.blit(shadow_surf, (shadow_x, 103))
    
    # Draw main title
    title_surf = font_title.render(title_text, True, BLOOD_RED)
    title_x = (SCREEN_WIDTH - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, 100))
    
    # Add glowing effect to title
    glow_factor = 0.5 + 0.5 * math.sin(current_time * 2)
    glow_size = int(10 * glow_factor)
    if glow_size > 0:
        # Create glow surface
        glow_surf = pygame.Surface((title_surf.get_width() + glow_size*2, 
                                   title_surf.get_height() + glow_size*2), pygame.SRCALPHA)
        for i in range(glow_size, 0, -1):
            alpha = 10
            pygame.draw.rect(glow_surf, (*BLOOD_RED[:3], alpha),
                           (glow_size-i, glow_size-i, 
                            title_surf.get_width()+i*2, 
                            title_surf.get_height()+i*2), 
                           1)
        screen.blit(glow_surf, (title_x - glow_size, 100 - glow_size))
    
    # Subtitle
    subtitle_text = "a roguelike adventure"
    subtitle_surf = ThemeManager.FONT_SUBHEADING.render(subtitle_text, True, BURNISHED_GOLD)
    subtitle_x = (SCREEN_WIDTH - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, 180))
    
    # Decorative line below subtitle
    line_width = 300
    line_x = (SCREEN_WIDTH - line_width) // 2
    pygame.draw.line(screen, BURNISHED_GOLD, (line_x, 220), (line_x + line_width, 220), 2)
    
    # Menu buttons
    buttons = ["New Game"]
    if show_resume:
        buttons.append("Resume Game")
    buttons.extend(["Options", "Exit Game"])
    
    button_width = 300
    button_height = 50
    button_spacing = 20
    total_buttons_height = len(buttons) * (button_height + button_spacing)
    
    # Starting y position for the first button (centered on screen)
    start_y = (SCREEN_HEIGHT - total_buttons_height) // 2 + 150
    
    for i, button_text in enumerate(buttons):
        button_y = start_y + i * (button_height + button_spacing)
        
        # Draw button using theme manager
        button_state = "active" if i == selected_index else "normal"
        button_surf = ThemeManager.create_button_surface(button_width, button_height, button_text, button_state)
        
        # Calculate position and draw button
        button_x = (SCREEN_WIDTH - button_width) // 2
        screen.blit(button_surf, (button_x, button_y))
        
        # If selected, add decorative elements
        if i == selected_index:
            # Draw selection indicators (golden triangles)
            indicator_size = 20
            left_x = button_x - 30
            right_x = button_x + button_width + 10
            center_y = button_y + button_height // 2
            
            # Left triangle
            pygame.draw.polygon(screen, BURNISHED_GOLD, [
                (left_x, center_y),
                (left_x + indicator_size, center_y - indicator_size // 2),
                (left_x + indicator_size, center_y + indicator_size // 2)
            ])
            
            # Right triangle
            pygame.draw.polygon(screen, BURNISHED_GOLD, [
                (right_x + indicator_size, center_y),
                (right_x, center_y - indicator_size // 2),
                (right_x, center_y + indicator_size // 2)
            ])
    
    # Add version info at bottom
    version_text = "Version 0.1 Alpha"
    version_surf = ThemeManager.FONT_SMALL.render(version_text, True, UI_TEXT_PRIMARY)
    screen.blit(version_surf, (20, SCREEN_HEIGHT - 30))
    
    # Update the display
    pygame.display.flip()

def title_screen(show_resume=False):
    """Show the title screen and handle input until user makes a selection"""
    # Initialize pygame if not already done
    if not pygame.get_init():
        pygame.init()
    
    # Set up the clock
    clock = pygame.time.Clock()
    
    # Current selected button
    selected_index = 0
    
    # Get the button count
    button_count = 3 if not show_resume else 4
    
    # Draw initial screen
    draw_title_screen(selected_index, show_resume)
    
    # Main title screen loop
    running = True
    while running:
        # Cap the frame rate
        clock.tick(30)
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    # Move selection up
                    selected_index = (selected_index - 1) % button_count
                    draw_title_screen(selected_index, show_resume)
                
                elif event.key == pygame.K_DOWN:
                    # Move selection down
                    selected_index = (selected_index + 1) % button_count
                    draw_title_screen(selected_index, show_resume)
                
                elif event.key == pygame.K_RETURN:
                    # Process selection
                    if not show_resume:
                        # Regular menu (no resume option)
                        if selected_index == 0:
                            # New Game selected
                            return "new_game"
                        elif selected_index == 1:
                            # Options selected - not implemented yet
                            pass
                        elif selected_index == 2:
                            # Exit Game selected
                            pygame.quit()
                            sys.exit()
                    else:
                        # Menu with resume option
                        if selected_index == 0:
                            # New Game selected
                            return "new_game"
                        elif selected_index == 1:
                            # Resume Game selected
                            return "resume_game"
                        elif selected_index == 2:
                            # Options selected - not implemented yet
                            pass
                        elif selected_index == 3:
                            # Exit Game selected
                            pygame.quit()
                            sys.exit()
                
                elif event.key == pygame.K_ESCAPE:
                    # Exit on escape
                    pygame.quit()
                    sys.exit()
        
        # Redraw title screen every frame to show animations
        draw_title_screen(selected_index, show_resume)
    
    # This should not be reached
    return None
