import pygame
import sys
from ..config import screen, BLACK, WHITE, RED, YELLOW

def draw_title_screen(selected_index):
    """Draw the title screen with the given button selected"""
    # Fill screen with black
    screen.fill(BLACK)
    
    # Game title
    font_title = pygame.font.SysFont('Arial', 72, bold=True)
    title_text = font_title.render("Crimson Depths", True, RED)
    title_x = (screen.get_width() - title_text.get_width()) // 2
    screen.blit(title_text, (title_x, 100))
    
    # Subtitle
    font_subtitle = pygame.font.SysFont('Arial', 24)
    subtitle_text = font_subtitle.render("by Cosmic", True, WHITE)
    subtitle_x = (screen.get_width() - subtitle_text.get_width()) // 2
    screen.blit(subtitle_text, (subtitle_x, 180))
    
    # Menu buttons
    buttons = ["New Game", "Load Game", "Options", "Exit Game"]
    font_button = pygame.font.SysFont('Arial', 36)
    
    button_width = 300
    button_height = 50
    button_spacing = 20
    total_buttons_height = len(buttons) * (button_height + button_spacing)
    
    # Starting y position for the first button (centered on screen)
    start_y = (screen.get_height() - total_buttons_height) // 2 + 100
    
    for i, button_text in enumerate(buttons):
        button_y = start_y + i * (button_height + button_spacing)
        button_rect = pygame.Rect(
            (screen.get_width() - button_width) // 2,
            button_y,
            button_width,
            button_height
        )
        
        # Determine button color (highlight if selected)
        if i == selected_index:
            # Draw selection indicator (yellow triangle)
            indicator_size = 20
            pygame.draw.polygon(screen, YELLOW, [
                (button_rect.left - 30, button_rect.centery),
                (button_rect.left - 30 + indicator_size, button_rect.centery - indicator_size // 2),
                (button_rect.left - 30 + indicator_size, button_rect.centery + indicator_size // 2)
            ])
            button_color = RED
        else:
            button_color = WHITE
        
        # Draw button text
        text = font_button.render(button_text, True, button_color)
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
    
    # Update the display
    pygame.display.flip()

def title_screen():
    """Show the title screen and handle input until user makes a selection"""
    # Initialize pygame if not already done
    if not pygame.get_init():
        pygame.init()
    
    # Set up the clock
    clock = pygame.time.Clock()
    
    # Current selected button
    selected_index = 0
    
    # Draw initial screen
    draw_title_screen(selected_index)
    
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
                    selected_index = (selected_index - 1) % 4
                    draw_title_screen(selected_index)
                
                elif event.key == pygame.K_DOWN:
                    # Move selection down
                    selected_index = (selected_index + 1) % 4
                    draw_title_screen(selected_index)
                
                elif event.key == pygame.K_RETURN:
                    # Process selection
                    if selected_index == 0:
                        # New Game selected
                        return "new_game"
                    elif selected_index == 1:
                        # Load Game selected - not implemented yet
                        pass
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
    
    # This should not be reached
    return None
