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
    ANIMATION_DURATION, PanelType, YELLOW, RED, DARK_GRAY, MESSAGE_LOG_HEIGHT, TILE_SIZE, INFO_PANEL_WIDTH,
    BLACK, LIGHT_BLUE, GREEN, EquipmentSlot
)
from ui.theme import ThemeManager

# Define a fixed height for the action bar in tiles
ACTION_BAR_HEIGHT = TILE_SIZE * 5

# Define a fixed height for the status bar in tiles
STATUS_BAR_HEIGHT = TILE_SIZE * 2

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
            # Height between status bar and message log
            total_vertical = STATUS_BAR_HEIGHT + MESSAGE_LOG_HEIGHT * TILE_SIZE
            self.height = SCREEN_HEIGHT - total_vertical
            self.x = SCREEN_WIDTH - self.width
            self.y = STATUS_BAR_HEIGHT

        elif self.panel_type == PanelType.MESSAGE_LOG:
            # Bottom panel fixed height
            self.width = SCREEN_WIDTH - (INFO_PANEL_WIDTH * TILE_SIZE)
            self.height = MESSAGE_LOG_HEIGHT * TILE_SIZE
            self.x = 0
            self.y = SCREEN_HEIGHT - self.height

        elif self.panel_type == PanelType.STATUS_BAR:
            # Top status bar fixed height
            self.width = SCREEN_WIDTH
            self.height = STATUS_BAR_HEIGHT
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
            total_vertical = STATUS_BAR_HEIGHT + MESSAGE_LOG_HEIGHT * TILE_SIZE
            raw_h = SCREEN_HEIGHT - total_vertical
            self.height = (raw_h // TILE_SIZE) * TILE_SIZE
            self.x = 0
            self.y = STATUS_BAR_HEIGHT
    
    def _create_surfaces(self):
        """Create panel surfaces including header and content areas."""
        header_height = 40
        
        # Create header with title (without toggle button)
        self.header_surface = ThemeManager.create_panel_header(self.width, self.title)
        
        # Remove toggle button
        self.toggle_button_rect = None
        
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
        
        # We no longer draw a toggle button
        
        # Blit the panel to the screen
        screen.blit(panel_surface, (self.x, self.y))
    
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
        # No toggle button functionality since we removed it
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
        
        # Character level - displayed first
        char_level_text = f"Level: {player.fighter.level}"
        char_level_surf = ThemeManager.FONT_NORMAL.render(char_level_text, True, UI_HIGHLIGHT)
        self.content_surface.blit(char_level_surf, (margin, y_pos))
        y_pos += 35
        
        # Primary Attributes Grid
        attr_title = ThemeManager.FONT_NORMAL.render("ATTRIBUTES", True, UI_HIGHLIGHT)
        self.content_surface.blit(attr_title, (margin, y_pos))
        y_pos += 25
        
        # Calculate column width
        col_width = (self.width - (margin * 2)) // 3
        
        # First row: STR, DEX, CON
        row1_attrs = [("STR", player.fighter.str), 
                     ("DEX", player.fighter.dex), 
                     ("CON", player.fighter.con)]
        
        for i, (attr_name, attr_value) in enumerate(row1_attrs):
            attr_text = f"{attr_name}: {attr_value}"
            attr_surf = ThemeManager.FONT_NORMAL.render(attr_text, True, UI_TEXT_PRIMARY)
            x_pos = margin + (i * col_width)
            self.content_surface.blit(attr_surf, (x_pos, y_pos))
        
        y_pos += 25
        
        # Second row: INT, WIS, CHA
        row2_attrs = [("INT", player.fighter.int), 
                     ("WIS", player.fighter.wis), 
                     ("CHA", player.fighter.cha)]
        
        for i, (attr_name, attr_value) in enumerate(row2_attrs):
            attr_text = f"{attr_name}: {attr_value}"
            attr_surf = ThemeManager.FONT_NORMAL.render(attr_text, True, UI_TEXT_PRIMARY)
            x_pos = margin + (i * col_width)
            self.content_surface.blit(attr_surf, (x_pos, y_pos))
        
        y_pos += 40
        
        # Combat Information Card
        combat_title = ThemeManager.FONT_NORMAL.render("COMBAT STATS", True, UI_HIGHLIGHT)
        self.content_surface.blit(combat_title, (margin, y_pos))
        y_pos += 25
        
        # Draw a subtle border/background for the combat card
        card_width = self.width - (margin * 2)
        card_height = 110  # Adjust based on number of stats
        card_rect = pygame.Rect(margin - 5, y_pos - 5, card_width, card_height)
        pygame.draw.rect(self.content_surface, UI_BORDER, card_rect, 1, border_radius=3)
        
        # Combat stats
        combat_stats = [
            f"Attack Bonus: +{player.fighter.attack_bonus}",
            f"Critical Hit: {10}%",  # Placeholder for crit chance
            f"Dodge: {player.fighter.get_dodge_chance()}%",
            f"Armor: {player.fighter.armor}",
            f"Damage: {player.fighter.damage_dice[0]}d{player.fighter.damage_dice[1]}"
        ]
        
        for stat in combat_stats:
            stat_surf = ThemeManager.FONT_NORMAL.render(stat, True, UI_TEXT_PRIMARY)
            self.content_surface.blit(stat_surf, (margin, y_pos))
            y_pos += 20
        
        y_pos += 20
        
        # Equipment Information
        equip_title = ThemeManager.FONT_NORMAL.render("EQUIPMENT", True, UI_HIGHLIGHT)
        self.content_surface.blit(equip_title, (margin, y_pos))
        y_pos += 25
        
        # Right Hand
        right_hand = player.inventory.get_equipped_item(EquipmentSlot.RIGHT_HAND)
        right_hand_text = f"Right Hand: {right_hand.name if right_hand else 'Empty'}"
        right_hand_surf = ThemeManager.FONT_NORMAL.render(right_hand_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(right_hand_surf, (margin, y_pos))
        y_pos += 20
        
        # Left Hand
        left_hand = player.inventory.get_equipped_item(EquipmentSlot.LEFT_HAND)
        left_hand_text = f"Left Hand: {left_hand.name if left_hand else 'Empty'}"
        left_hand_surf = ThemeManager.FONT_NORMAL.render(left_hand_text, True, UI_TEXT_PRIMARY)
        self.content_surface.blit(left_hand_surf, (margin, y_pos))
        y_pos += 30
        
        # Silver pieces (currency) - moved to after equipment
        silver_text = f"Silver: {player.silver_pieces} sp"
        silver_surf = ThemeManager.FONT_NORMAL.render(silver_text, True, YELLOW)
        self.content_surface.blit(silver_surf, (margin, y_pos))

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

class StatusBarPanel(Panel):
    """Panel for displaying character status bars."""
    
    def __init__(self):
        super().__init__(PanelType.STATUS_BAR, "")
        # Override the default dimensions calculation to ensure content surface is created properly
        self._create_surfaces()
        
    def _create_surfaces(self):
        """Create the content surface directly without a header"""
        # Skip the header creation and toggle button
        self.header_surface = None
        self.toggle_button_rect = None
        
        # Create content surface to fill the entire panel
        self.content_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.content_surface.fill(BLACK)
    
    def update_content(self, player):
        """Update the status bar content with player information."""
        if not self.content_surface or not player:
            return
            
        # Clear the content area
        self.content_surface.fill(BLACK)
        
        # Calculate bar dimensions
        bar_height = 20
        bar_spacing = 10
        total_bars = 4  # HP, MP, XP, Ammo
        total_width = self.width - (bar_spacing * (total_bars + 1))
        bar_width = total_width // total_bars
        
        # Define a darker blue color for mana
        # RGB values for a medium/darker blue
        DARKER_BLUE = (0, 0, 180)
        
        # Draw health bar
        hp_x = bar_spacing
        hp_bar = ThemeManager.create_progress_bar(
            bar_width, bar_height, player.fighter.hp, player.fighter.max_hp,
            fg_color=RED, bg_color=DARK_GRAY, include_text=True
        )
        self.content_surface.blit(hp_bar, (hp_x, (self.height - bar_height) // 2))
        
        # Draw mana bar with darker blue
        mp_x = hp_x + bar_width + bar_spacing
        mp_bar = ThemeManager.create_progress_bar(
            bar_width, bar_height, player.fighter.mp, player.fighter.max_mp,
            fg_color=DARKER_BLUE, bg_color=DARK_GRAY, include_text=True
        )
        self.content_surface.blit(mp_bar, (mp_x, (self.height - bar_height) // 2))
        
        # Draw experience bar
        xp_x = mp_x + bar_width + bar_spacing
        next_level_xp = player.fighter.get_next_level_xp()
        if next_level_xp:
            xp_bar = ThemeManager.create_progress_bar(
                bar_width, bar_height, player.fighter.xp, next_level_xp,
                fg_color=YELLOW, bg_color=DARK_GRAY, include_text=True
            )
            self.content_surface.blit(xp_bar, (xp_x, (self.height - bar_height) // 2))
        
        # Draw ammo bar if ranged weapon is equipped
        ammo_x = xp_x + bar_width + bar_spacing
        ranged_weapon = player.inventory.get_equipped_ranged_weapon()
        ammo = player.inventory.get_ammo()
        if ranged_weapon and ammo:
            ammo_bar = ThemeManager.create_progress_bar(
                bar_width, bar_height, ammo.item.ammo_data.current, ammo.item.ammo_data.capacity,
                fg_color=GREEN, bg_color=DARK_GRAY, include_text=True
            )
            self.content_surface.blit(ammo_bar, (ammo_x, (self.height - bar_height) // 2))
    
    def render(self, screen):
        """Override render to directly blit the content surface"""
        if self.state == PANEL_STATE_HIDDEN:
            return
            
        # For the status bar, we just want to render the content
        screen.blit(self.content_surface, (self.x, self.y))

class PanelManager:
    """Manages all UI panels and their interactions."""
    
    def __init__(self):
        # Create panels
        self.character_panel = CharacterPanel()
        self.message_log_panel = MessageLogPanel()
        self.status_bar_panel = StatusBarPanel()
        
        # Map panel is special - it's the main display area defined by other panels
        self.map_panel = None  # This will be calculated based on other panels
        
        self.panels = [
            self.character_panel,
            self.message_log_panel, 
            self.status_bar_panel
        ]
        
        # Calculate map panel area
        self._calculate_map_area()
    
    def _calculate_map_area(self):
        """Calculate the map display area based on other panels."""
        # Calculate map area boundaries between status bar and message log panel
        map_x = 0
        map_y = self.status_bar_panel.height
        map_width = SCREEN_WIDTH - self.character_panel.width
        # Map height spans from bottom of status bar to top of message log panel
        map_height = SCREEN_HEIGHT - self.message_log_panel.height - self.status_bar_panel.height
        
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
        if player:
            self.character_panel.update_content(player, game_world)
            self.status_bar_panel.update_content(player)
            
        if message_log:
            self.message_log_panel.update_content(message_log)
        
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