"""
Panel system for responsive UI layout in Crimson Depths.
This module provides UI panel components with collapsible/expandable functionality.
"""

import pygame
import time
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_RIGHT_WIDTH_PCT, PANEL_TOP_HEIGHT_PCT,
    PANEL_MIN_WIDTH_PX, PANEL_MIN_HEIGHT_PX,
    PANEL_STATE_EXPANDED, PANEL_STATE_COLLAPSED, PANEL_STATE_HIDDEN,
    UI_PANEL_BACKGROUND, UI_BORDER, UI_HIGHLIGHT, UI_TEXT_PRIMARY,
    ANIMATION_DURATION, PanelType, YELLOW, RED, DARK_GRAY, MESSAGE_LOG_HEIGHT, TILE_SIZE, INFO_PANEL_WIDTH
)
from ui.theme import ThemeManager

# Define a fixed height for the action bar in tiles
ACTION_BAR_HEIGHT = TILE_SIZE * 5

class Panel:
    """Base class for UI panels with responsive positioning and state handling."""
    
    def __init__(self, panel_type, title="Panel"):
        self.panel_type = panel_type
        self.title = title
        self.state = PANEL_STATE_EXPANDED
        self.animation_state = None  # Can be None, "expanding", "collapsing", etc.
        self.animation_start_time = 0
        self.collapsed_size = 40  # Height of collapsed panel (showing just header)
        self.content_surface = None
        self.header_surface = None
        self.toggle_button_rect = None
        
        # Set initial dimensions based on panel type
        self._calculate_dimensions()
        
        # Create initial surfaces
        self._create_surfaces()
    
    def _calculate_dimensions(self):
        """Calculate panel dimensions based on tile grid."""
        if self.panel_type == PanelType.CHARACTER:
            # Right side character panel
            self.width = INFO_PANEL_WIDTH * TILE_SIZE
            # Height between action bar and message log
            total_vertical = ACTION_BAR_HEIGHT + MESSAGE_LOG_HEIGHT * TILE_SIZE
            self.height = SCREEN_HEIGHT - total_vertical
            self.x = SCREEN_WIDTH - self.width
            self.y = ACTION_BAR_HEIGHT

        elif self.panel_type == PanelType.MESSAGE_LOG:
            # Bottom panel fixed height
            self.width = SCREEN_WIDTH - (INFO_PANEL_WIDTH * TILE_SIZE)
            self.height = MESSAGE_LOG_HEIGHT * TILE_SIZE
            self.x = 0
            self.y = SCREEN_HEIGHT - self.height

        elif self.panel_type == PanelType.ACTION_BAR:
            # Top action bar fixed height
            self.width = SCREEN_WIDTH
            self.height = ACTION_BAR_HEIGHT
            self.x = 0
            self.y = 0

        elif self.panel_type == PanelType.INVENTORY:
            # Floating inventory aligned to grid
            inv_w_tiles = int((SCREEN_WIDTH * 0.6) // TILE_SIZE)
            inv_h_tiles = int((SCREEN_HEIGHT * 0.7) // TILE_SIZE)
            self.width = inv_w_tiles * TILE_SIZE
            self.height = inv_h_tiles * TILE_SIZE
            self.x = (SCREEN_WIDTH - self.width) // 2
            self.y = (SCREEN_HEIGHT - self.height) // 2

        else:
            # Fallback default
            self.width = SCREEN_WIDTH - (INFO_PANEL_WIDTH * TILE_SIZE)
            total_vertical = ACTION_BAR_HEIGHT + MESSAGE_LOG_HEIGHT * TILE_SIZE
            raw_h = SCREEN_HEIGHT - total_vertical
            self.height = (raw_h // TILE_SIZE) * TILE_SIZE
            self.x = 0
            self.y = ACTION_BAR_HEIGHT
    
    def _create_surfaces(self):
        """Create panel surfaces including header and content areas."""
        header_height = 40
        
        # Create header with title and toggle button
        self.header_surface = ThemeManager.create_panel_header(self.width, self.title)
        
        # Create toggle button in the header
        button_size = 30
        button_x = self.width - button_size - 5
        button_y = (header_height - button_size) // 2
        self.toggle_button_rect = pygame.Rect(button_x, button_y, button_size, button_size)
        
        # Create content area
        content_height = self.height - header_height
        if content_height > 0:
            self.content_surface = pygame.Surface((self.width, content_height), pygame.SRCALPHA)
            self.content_surface.fill(UI_PANEL_BACKGROUND)
    
    def update(self):
        """Update panel animation state and dimensions if needed."""
        if self.animation_state:
            current_time = time.time() * 1000  # Current time in milliseconds
            elapsed = current_time - self.animation_start_time
            duration = ANIMATION_DURATION
            
            if elapsed >= duration:
                # Animation complete
                if self.animation_state == "collapsing":
                    self.state = PANEL_STATE_COLLAPSED
                elif self.animation_state == "expanding":
                    self.state = PANEL_STATE_EXPANDED
                elif self.animation_state == "fading_out":
                    self.state = PANEL_STATE_HIDDEN
                elif self.animation_state == "fading_in":
                    self.state = PANEL_STATE_EXPANDED
                
                self.animation_state = None
            
            # If screen size changed, recalculate dimensions
            self._calculate_dimensions()
    
    def render(self, screen):
        """Render the panel to the screen."""
        if self.state == PANEL_STATE_HIDDEN:
            return
            
        # Create the main panel surface
        if self.state == PANEL_STATE_COLLAPSED:
            # Only show header when collapsed
            panel_height = self.collapsed_size
            panel_surface = pygame.Surface((self.width, panel_height), pygame.SRCALPHA)
            panel_surface.blit(self.header_surface, (0, 0))
        else:
            # Show full panel when expanded
            panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            panel_surface.blit(self.header_surface, (0, 0))
            
            if self.content_surface:
                panel_surface.blit(self.content_surface, (0, self.header_surface.get_height()))
        
        # Apply animation effects if needed
        if self.animation_state:
            current_time = time.time() * 1000
            elapsed = current_time - self.animation_start_time
            progress = min(1.0, elapsed / ANIMATION_DURATION)
            
            panel_surface = ThemeManager.apply_panel_animation(
                panel_surface, self.animation_state, progress
            )
        
        # Draw the toggle button in the header
        self._draw_toggle_button(panel_surface)
        
        # Blit the panel to the screen
        screen.blit(panel_surface, (self.x, self.y))
    
    def _draw_toggle_button(self, surface):
        """Draw the collapse/expand toggle button."""
        button_rect = self.toggle_button_rect
        
        # Draw button background
        pygame.draw.rect(surface, UI_BORDER, button_rect, border_radius=3)
        
        # Draw appropriate icon based on current state
        if self.state == PANEL_STATE_EXPANDED or self.animation_state == "expanding":
            # Draw collapse icon (down arrow)
            points = [
                (button_rect.centerx - 6, button_rect.centery - 3),
                (button_rect.centerx + 6, button_rect.centery - 3),
                (button_rect.centerx, button_rect.centery + 5)
            ]
        else:
            # Draw expand icon (right arrow)
            points = [
                (button_rect.centerx - 5, button_rect.centery - 6),
                (button_rect.centerx + 3, button_rect.centery),
                (button_rect.centerx - 5, button_rect.centery + 6)
            ]
            
        pygame.draw.polygon(surface, UI_TEXT_PRIMARY, points)
    
    def toggle_state(self):
        """Toggle between expanded and collapsed states with animation."""
        if self.animation_state:
            # Don't allow toggling during animation
            return
            
        if self.state == PANEL_STATE_EXPANDED:
            # Collapse the panel
            self.animation_state = "collapsing"
            self.animation_start_time = time.time() * 1000
        elif self.state == PANEL_STATE_COLLAPSED:
            # Expand the panel
            self.animation_state = "expanding"
            self.animation_start_time = time.time() * 1000
        elif self.state == PANEL_STATE_HIDDEN:
            # Show the panel
            self.animation_state = "fading_in"
            self.animation_start_time = time.time() * 1000
    
    def hide(self):
        """Hide the panel with animation."""
        if self.state != PANEL_STATE_HIDDEN and not self.animation_state:
            self.animation_state = "fading_out"
            self.animation_start_time = time.time() * 1000
    
    def handle_event(self, event):
        """Handle panel-related input events."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            # Adjust mouse position to be relative to panel
            relative_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            # Check if toggle button was clicked
            if (self.toggle_button_rect and 
                0 <= relative_pos[0] < self.width and 
                0 <= relative_pos[1] < self.collapsed_size):
                
                if self.toggle_button_rect.collidepoint(relative_pos):
                    self.toggle_state()
                    return True  # Event was handled
        
        return False  # Event was not handled

class CharacterPanel(Panel):
    """Panel for displaying character information."""
    
    def __init__(self):
        super().__init__(PanelType.CHARACTER, "CHARACTER")
        
    def update_content(self, player, game_world):
        """Update the character panel content with player information."""
        if not self.content_surface:
            return
            
        # Clear the content area
        self.content_surface.fill(UI_PANEL_BACKGROUND)
        
        if not player:
            return
            
        # Draw character information
        margin = 20
        y_pos = margin
        
        # Dungeon level information
        level_text = f"Dungeon: {game_world.current_level}"
        level_surf = ThemeManager.FONT_NORMAL.render(level_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(level_surf, (margin, y_pos))
        y_pos += 25
        
        # Character level
        char_level_text = f"Character Level: {player.fighter.level}"
        char_level_surf = ThemeManager.FONT_NORMAL.render(char_level_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(char_level_surf, (margin, y_pos))
        y_pos += 25
        
        # Silver pieces
        silver_text = f"Silver: {player.silver_pieces} sp"
        silver_surf = ThemeManager.FONT_NORMAL.render(silver_text, True, UI_HIGHLIGHT)
        self.content_surface.blit(silver_surf, (margin, y_pos))
        y_pos += 35
        
        # XP information
        xp_text = f"Experience: {player.fighter.xp}"
        xp_surf = ThemeManager.FONT_NORMAL.render(xp_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(xp_surf, (margin, y_pos))
        y_pos += 20
        
        # XP progress bar
        next_level_xp = player.fighter.get_next_level_xp()
        if next_level_xp:
            bar_width = self.width - (margin * 2)
            xp_bar = ThemeManager.create_progress_bar(
                bar_width, 15, player.fighter.xp, next_level_xp, 
                fg_color=YELLOW, include_text=False
            )
            self.content_surface.blit(xp_bar, (margin, y_pos))
            
            # XP remaining text
            xp_remaining = next_level_xp - player.fighter.xp
            xp_remaining_text = f"Next level: {xp_remaining} XP needed"
            xp_remaining_surf = ThemeManager.FONT_SMALL.render(xp_remaining_text, True, UI_TEXT_PRIMARY)
            self.content_surface.blit(xp_remaining_surf, (margin, y_pos + 20))
            y_pos += 45
        else:
            y_pos += 25
            
        # Health information
        hp_text = f"Health"
        hp_surf = ThemeManager.FONT_NORMAL.render(hp_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(hp_surf, (margin, y_pos))
        y_pos += 20
        
        # Health progress bar
        bar_width = self.width - (margin * 2)
        hp_bar = ThemeManager.create_progress_bar(
            bar_width, 20, player.fighter.hp, player.fighter.max_hp, 
            fg_color=RED, bg_color=DARK_GRAY
        )
        self.content_surface.blit(hp_bar, (margin, y_pos))
        y_pos += 35
        
        # Combat statistics
        stats_text = "COMBAT STATS"
        stats_surf = ThemeManager.FONT_NORMAL.render(stats_text, True, UI_HIGHLIGHT)
        self.content_surface.blit(stats_surf, (margin, y_pos))
        y_pos += 25
        
        # Display armor
        armor_text = f"Armor Class: {player.fighter.armor}"
        armor_surf = ThemeManager.FONT_NORMAL.render(armor_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(armor_surf, (margin, y_pos))
        y_pos += 20
        
        # Display damage
        damage_text = f"Damage: {player.fighter.damage_dice[0]}d{player.fighter.damage_dice[1]}"
        damage_surf = ThemeManager.FONT_NORMAL.render(damage_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(damage_surf, (margin, y_pos))

class MessageLogPanel(Panel):
    """Panel for displaying game messages."""
    
    def __init__(self):
        super().__init__(PanelType.MESSAGE_LOG, "MESSAGE LOG")
        self.scroll_offset = 0
        self.max_visible_messages = 0
        self.message_log = None
        
    def update_content(self, message_log):
        """Update message log content with messages."""
        if not self.content_surface or not message_log:
            return
            
        # Store the message log for use in handle_event
        self.message_log = message_log
            
        # Clear the content area
        self.content_surface.fill(UI_PANEL_BACKGROUND)
        
        # Calculate how many messages can be displayed
        message_height = 20
        content_height = self.content_surface.get_height()
        self.max_visible_messages = content_height // message_height
        
        # Get messages to display based on scroll offset
        messages = list(message_log.messages)
        start_idx = max(0, len(messages) - self.max_visible_messages - self.scroll_offset)
        visible_messages = messages[start_idx:start_idx + self.max_visible_messages]
        
        # Draw messages
        y_pos = 5
        for message in visible_messages:
            message_surf = ThemeManager.FONT_NORMAL.render(message.text, True, message.color)
            self.content_surface.blit(message_surf, (10, y_pos))
            y_pos += message_height
            
    def handle_event(self, event):
        """Handle message log panel events including scrolling."""
        if super().handle_event(event):
            return True
            
        if event.type == pygame.MOUSEBUTTONDOWN and self.message_log:
            mouse_pos = pygame.mouse.get_pos()
            # Check if mouse is over this panel
            if (self.x <= mouse_pos[0] < self.x + self.width and 
                self.y <= mouse_pos[1] < self.y + self.height):
                
                if event.button == 4:  # Scroll up
                    self.scroll_offset = min(len(list(self.message_log.messages)) - self.max_visible_messages, 
                                           self.scroll_offset + 1)
                    return True
                elif event.button == 5:  # Scroll down
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                    return True
                    
        return False

class ActionBarPanel(Panel):
    """Panel for displaying action buttons and game controls."""
    
    def __init__(self):
        super().__init__(PanelType.ACTION_BAR, "")
        self.buttons = []
        self._create_buttons()
        
    def _create_buttons(self):
        """Create action bar buttons."""
        button_width = 120
        button_height = 30
        button_spacing = 10
        
        # Define buttons and their positions
        button_definitions = [
            {"text": "Inventory [I]", "x": 10},
            {"text": "Character [C]", "x": 10 + button_width + button_spacing},
            {"text": "Auto-explore [E]", "x": 10 + (button_width + button_spacing) * 2},
            {"text": "Target [T]", "x": 10 + (button_width + button_spacing) * 3},
            {"text": "Quick Fire [F]", "x": 10 + (button_width + button_spacing) * 4},
            {"text": "View Map [M]", "x": self.width - button_width - 10}
        ]
        
        # Create button objects
        for btn in button_definitions:
            y_pos = (self.height - button_height) // 2
            self.buttons.append({
                "rect": pygame.Rect(btn["x"], y_pos, button_width, button_height),
                "text": btn["text"],
                "state": "normal"
            })
    
    def update_content(self):
        """Update the action bar content."""
        if not self.content_surface:
            return
            
        # Clear the content area
        self.content_surface.fill(UI_PANEL_BACKGROUND)
        
        # Draw buttons
        for button in self.buttons:
            button_surf = ThemeManager.create_button_surface(
                button["rect"].width, 
                button["rect"].height,
                button["text"],
                button["state"]
            )
            self.content_surface.blit(button_surf, (button["rect"].x, button["rect"].y))
            
    def handle_event(self, event):
        """Handle action bar events and button clicks."""
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            relative_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            # Update button hover states
            for button in self.buttons:
                if button["rect"].collidepoint(relative_pos):
                    button["state"] = "hover"
                else:
                    button["state"] = "normal"
            
            # Update the content to reflect new button states
            self.update_content()
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            relative_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            # Check for button clicks
            for button in self.buttons:
                if button["rect"].collidepoint(relative_pos):
                    button["state"] = "active"
                    self.update_content()
                    
                    # Return the button text to identify which button was clicked
                    return button["text"]
            
        return None  # No button was clicked

class PanelManager:
    """Manages all UI panels and their interactions."""
    
    def __init__(self):
        # Create panels
        self.character_panel = CharacterPanel()
        self.message_log_panel = MessageLogPanel()
        self.action_bar_panel = ActionBarPanel()
        
        # Map panel is special - it's the main display area defined by other panels
        self.map_panel = None  # This will be calculated based on other panels
        
        self.panels = [
            self.character_panel,
            self.message_log_panel, 
            self.action_bar_panel
        ]
        
        # Calculate map panel area
        self._calculate_map_area()
    
    def _calculate_map_area(self):
        """Calculate the map display area based on other panels."""
        # Calculate map area boundaries between action bar and message log panel
        map_x = 0
        map_y = self.action_bar_panel.height
        map_width = SCREEN_WIDTH - self.character_panel.width
        # Map height spans from bottom of action bar to top of message log panel
        map_height = SCREEN_HEIGHT - self.message_log_panel.height - self.action_bar_panel.height
        
        self.map_area = {
            "x": map_x,
            "y": map_y,
            "width": map_width,
            "height": map_height
        }
    
    def update(self, player=None, game_world=None, message_log=None):
        """Update all panels with game state information."""
        for panel in self.panels:
            panel.update()
            
        # Update specific panel content if data provided
        if player and game_world:
            self.character_panel.update_content(player, game_world)
            
        if message_log:
            self.message_log_panel.update_content(message_log)
            
        self.action_bar_panel.update_content()
        
        # Recalculate map area in case panel dimensions changed
        self._calculate_map_area()
    
    def render(self, screen):
        """Render all panels to the screen."""
        for panel in self.panels:
            panel.render(screen)
    
    def handle_event(self, event):
        """Handle events for all panels."""
        result = None
        
        for panel in self.panels:
            panel_result = panel.handle_event(event)
            if panel_result:
                # If the panel returned a value, store it
                result = panel_result
                
        return result
    
    def get_map_dimensions(self):
        """Get the current map viewing area dimensions."""
        return self.map_area 