"""
Theme system for Crimson Depths UI.
This module manages the UI theming, styling, and animation effects.
"""

import pygame
import math
from config import (
    UI_BACKGROUND, UI_BORDER, UI_TEXT_PRIMARY, UI_TEXT_SECONDARY, 
    UI_HIGHLIGHT, UI_PANEL_BACKGROUND, UI_BUTTON_NORMAL, UI_BUTTON_HOVER,
    UI_BUTTON_ACTIVE, DEEP_CRIMSON, DARK_PURPLE, OBSIDIAN_BLACK, 
    BURNISHED_GOLD, BLOOD_RED, MYSTICAL_BLUE, ETHEREAL_GREEN,
    ANIMATION_DURATION, DARK_GRAY, RED, BLACK
)

# Initialize pygame font system
pygame.font.init()

class ThemeManager:
    """Manages UI theme, styling, and animations."""
    
    # Font definitions as class variables
    FONT_HEADING = pygame.font.SysFont('Arial', 32, bold=True)
    FONT_SUBHEADING = pygame.font.SysFont('Arial', 24, bold=True)
    FONT_NORMAL = pygame.font.SysFont('Arial', 14)
    FONT_SMALL = pygame.font.SysFont('Arial', 12)
    
    @staticmethod
    def create_bordered_surface(width, height, bg_color=UI_PANEL_BACKGROUND, border_color=UI_BORDER, border_width=2):
        """Create a surface with a background color and border."""
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # Fill background
        pygame.draw.rect(surface, bg_color, (0, 0, width, height))
        # Draw border
        pygame.draw.rect(surface, border_color, (0, 0, width, height), border_width)
        return surface
    
    @staticmethod
    def create_button_surface(width, height, text, state="normal"):
        """Create a button surface with appropriate styling based on state."""
        # Select color based on button state
        if state == "hover":
            bg_color = UI_BUTTON_HOVER
        elif state == "active":
            bg_color = UI_BUTTON_ACTIVE
        else:  # normal
            bg_color = UI_BUTTON_NORMAL
            
        # Create the button surface
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw button background with rounded corners
        pygame.draw.rect(surface, bg_color, (0, 0, width, height), border_radius=5)
        
        # Add a subtle gradient effect
        for i in range(height // 2):
            alpha = 100 - (i * 2)  # Decreasing alpha for gradient effect
            if alpha < 0:
                alpha = 0
            highlight_color = (*bg_color[:3], alpha)  # Create color with alpha
            pygame.draw.rect(surface, highlight_color, (1, i, width - 2, 1))
            
        # Add button text
        text_surf = ThemeManager.FONT_NORMAL.render(text, True, UI_TEXT_PRIMARY)
        text_rect = text_surf.get_rect(center=(width // 2, height // 2))
        surface.blit(text_surf, text_rect)
        
        # Add border glow effect on hover/active
        if state != "normal":
            pygame.draw.rect(surface, UI_HIGHLIGHT, (0, 0, width, height), 2, border_radius=5)
            
        return surface
    
    @staticmethod
    def create_panel_header(width, text, bg_color=BLACK, text_color=RED):
        """Create a panel header with title text."""
        header_height = 40
        surface = pygame.Surface((width, header_height), pygame.SRCALPHA)
        
        # Draw header background
        pygame.draw.rect(surface, bg_color, (0, 0, width, header_height))
        
        # Add decorative elements
        pygame.draw.line(surface, BURNISHED_GOLD, (10, header_height - 4), (width - 10, header_height - 4), 2)
        
        # Add header text
        text_surf = ThemeManager.FONT_SUBHEADING.render(text, True, text_color)
        text_rect = text_surf.get_rect(midleft=(20, header_height // 2))
        surface.blit(text_surf, text_rect)
        
        return surface
    
    @staticmethod
    def create_progress_bar(width, height, value, max_value, fg_color=BLOOD_RED, bg_color=DARK_GRAY, include_text=True):
        """Create a stylized progress bar."""
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw background
        pygame.draw.rect(surface, bg_color, (0, 0, width, height), border_radius=3)
        
        # Calculate filled width
        if max_value > 0:  # Avoid division by zero
            filled_width = int((value / max_value) * width)
        else:
            filled_width = 0
            
        # Draw filled portion
        if filled_width > 0:
            pygame.draw.rect(surface, fg_color, (0, 0, filled_width, height), border_radius=3)
            
        # Add text if requested
        if include_text:
            text = f"{value}/{max_value}" 
            text_surf = ThemeManager.FONT_SMALL.render(text, True, UI_TEXT_PRIMARY)
            text_rect = text_surf.get_rect(center=(width // 2, height // 2))
            surface.blit(text_surf, text_rect)
            
        return surface

    @staticmethod
    def apply_panel_animation(panel_surface, state, progress):
        """Apply animation effect to panel based on state and animation progress."""
        if state == "expanding" or state == "collapsing":
            # Scale animation
            progress = ThemeManager._ease_out_quad(progress)
            if state == "collapsing":
                progress = 1 - progress
                
            # Scale the surface
            original_size = panel_surface.get_size()
            new_width = int(original_size[0] * progress)
            new_height = original_size[1]  # Keep height the same
            
            if new_width <= 0:  # Avoid zero width
                new_width = 1
                
            return pygame.transform.scale(panel_surface, (new_width, new_height))
        
        elif state == "fading_in" or state == "fading_out":
            # Alpha animation
            progress = ThemeManager._ease_out_quad(progress)
            if state == "fading_out":
                progress = 1 - progress
                
            # Set alpha for the surface
            alpha_surface = panel_surface.copy()
            alpha_surface.set_alpha(int(255 * progress))
            return alpha_surface
            
        # No animation, return original surface
        return panel_surface
    
    @staticmethod
    def _ease_out_quad(t):
        """Quadratic ease-out function. t should be between 0 and 1."""
        return t * (2 - t)
    
    @staticmethod
    def _ease_in_out_cubic(t):
        """Cubic ease-in-out function. t should be between 0 and 1."""
        return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2 