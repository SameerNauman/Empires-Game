import sys
import pygame
from renderer import Renderer
from config import *

class StartUp:
    def __init__(self, screen, game_state_manager, asset_manager):
        self.display = screen
        self.game_state_manager = game_state_manager
        self.assets = asset_manager
        self.renderer = Renderer(self.display, self.assets)

        self.startup2_init()

        # Independent scroll and target positions for both carousels
        self.target_scroll_pos = [0.0, 0.0]
        self.scroll_pos = [0.0, 0.0]
        self.slot_width = 320

        # Stored choices
        self.player_faction = None
        self.enemy_faction = None
        self.player_color = "blue"
        self.enemy_color = "red"

    # Startup v1

    # Initializes variables for startup 1
    def startup1_init(self):
        # Available factions list
        self.factions = ["Seljuks", "Byzantines"]
        self.faction_descriptions = {
            "Seljuks": "Masters of cavalry warfare and swift raiding tactics, emphasizing mobile archery and heavy shock charges.",
            "Byzantines": "Heirs to the Roman legacy, relying on disciplined defensive lines, Varangian guards, and advanced engineering."
        }
        
        # Focus index: 0 = P1 Faction, 1 = P2 Faction, 2 = Main Menu Button
        self.focus_index = 0
        
        # Independent scroll and target positions for both carousels
        self.target_scroll_pos = [0.0, 0.0]
        self.scroll_pos = [0.0, 0.0]
        self.slot_width = 320

    def startup1_events(self, event):
        if event.key in [pygame.K_w, pygame.K_UP]:
            self.focus_index = max(0, self.focus_index - 1)
        elif event.key in [pygame.K_s, pygame.K_DOWN]:
            self.focus_index = min(2, self.focus_index + 1) # Max index is now 2 (Menu button)

        # Cycle left/right only if focused on carousels (0 or 1)
        elif event.key in [pygame.K_a, pygame.K_LEFT]:
            if self.focus_index < 2:
                self.target_scroll_pos[self.focus_index] -= 1.0
        elif event.key in [pygame.K_d, pygame.K_RIGHT]:
            if self.focus_index < 2:
                self.target_scroll_pos[self.focus_index] += 1.0

        # Confirm selection (LSHIFT)
        elif event.key == pygame.K_LSHIFT:
            if self.focus_index == 2:
                self.go_back()
            else:
                self.confirm_selection()

    # Confirms selection in carousel and begins the game
    def confirm_selection(self):
        if hasattr(self, 'p1_faction_idx'):
            p1_faction = self.factions[self.p1_faction_idx]
            p2_faction = self.factions[self.p2_faction_idx]
            p1_color = self.colors[self.p1_color_idx]
            p2_color = self.colors[self.p2_color_idx]
        else:
            p1_idx = int(round(self.target_scroll_pos[0])) % len(self.factions)
            p2_idx = int(round(self.target_scroll_pos[1])) % len(self.factions)
            p1_faction = self.factions[p1_idx]
            p2_faction = self.factions[p2_idx]
            p1_color = self.colors[0]
            p2_color = self.colors[1]

        self.player_faction = p1_faction.lower()
        self.enemy_faction = p2_faction.lower()
        self.player_color = p1_color.lower()
        self.enemy_color = p2_color.lower()

        # Reload assets in place using the shared reference
        self.assets.reload_factions(
            self.player_faction, 
            self.enemy_faction, 
            self.player_color, 
            self.enemy_color
        )

        self.game_state_manager.set_state(
            "gameplay state", 
            use_fade=True,
            player_faction=self.player_faction,
            enemy_faction=self.enemy_faction,
            player_color=self.player_color,
            enemy_color=self.enemy_color
        )

    # Main menu button in startup 1
    def go_back(self):
        self.game_state_manager.set_state("menu", use_fade=True)

    # Startup 2

    # Startup2 init
    def startup2_init(self):
        self.factions = ["Seljuks", "Byzantines"]
        self.colors = ["Blue", "Red", "Green", "Gold"]

        self.faction_descriptions = {
            "Seljuks": "Masters of cavalry warfare and swift raiding tactics, emphasizing mobile archery and heavy shock charges.",
            "Byzantines": "Heirs to the Roman legacy, relying on disciplined defensive lines, Varangian guards, and advanced engineering."
        }

        self.p1_faction_idx = 0
        self.p1_color_idx = 0
        self.p2_faction_idx = 1
        self.p2_color_idx = 1

        # Grid Navigation Matrix:
        # Row 0: Faction Selector (Col 0: P1, Col 2: P2)
        # Row 1: Color Selector  (Col 0: P1, Col 2: P2)
        # Row 2: Confirm Button  (Row-spanning)
        # Row 3: Main Menu Button (Row-spanning)
        self.selected_row = 0
        self.selected_col = 0  # 0 = Player 1 column, 2 = Player 2 column

        self.is_editing = False  # True when LSHIFT is pressed to modify value with A/D

    def startup2_events(self, event):
        # 1. Active Edit Mode (Cycle values with A/D)
        if self.is_editing:
            if event.key in [pygame.K_a, pygame.K_LEFT]:
                self.change_active_value(-1)
            elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                self.change_active_value(1)
            elif event.key in [pygame.K_LSHIFT, pygame.K_RETURN, pygame.K_ESCAPE]:
                self.is_editing = False
            return

        # 2. Standard WASD Navigation (Max row is now 3)
        if event.key in [pygame.K_w, pygame.K_UP]:
            self.selected_row = max(0, self.selected_row - 1)
        elif event.key in [pygame.K_s, pygame.K_DOWN]:
            self.selected_row = min(3, self.selected_row + 1)
        
        elif event.key in [pygame.K_a, pygame.K_LEFT]:
            if self.selected_row < 2:
                self.selected_col = 0
        elif event.key in [pygame.K_d, pygame.K_RIGHT]:
            if self.selected_row < 2:
                self.selected_col = 2

        # 3. LSHIFT Action Trigger
        elif event.key == pygame.K_LSHIFT:
            if self.selected_row == 2:
                self.confirm_selection()
            elif self.selected_row == 3:
                self.go_back()
            else:
                self.is_editing = True  # Enter edit mode for Faction/Color

    def change_active_value(self, delta):
        if self.selected_row == 0:
            if self.selected_col == 0:
                self.p1_faction_idx = (self.p1_faction_idx + delta) % len(self.factions)
            else:
                self.p2_faction_idx = (self.p2_faction_idx + delta) % len(self.factions)
        elif self.selected_row == 1:
            if self.selected_col == 0:
                self.p1_color_idx = (self.p1_color_idx + delta) % len(self.colors)
            else:
                self.p2_color_idx = (self.p2_color_idx + delta) % len(self.colors)

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def run(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_game()
            
            if event.type == pygame.KEYDOWN:
                self.startup2_events(event)
                    
        self.renderer.draw_startup2(self)