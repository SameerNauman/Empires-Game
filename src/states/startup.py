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

        # Stored choices
        self.player_faction = None
        self.enemy_faction = None
        self.player_color = "blue"
        self.enemy_color = "red"

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def confirm_selection(self):
        """Locks in both selections and launches gameplay state."""
        p1_idx = int(round(self.target_scroll_pos[0])) % len(self.factions)
        p2_idx = int(round(self.target_scroll_pos[1])) % len(self.factions)

        self.player_faction = self.factions[p1_idx].lower()
        self.enemy_faction = self.factions[p2_idx].lower()

        self.game_state_manager.set_state(
            "gameplay state", 
            use_fade=True,
            player_faction=self.player_faction,
            enemy_faction=self.enemy_faction,
            player_color=self.player_color,
            enemy_color=self.enemy_color
        )

    def go_back(self):
        self.game_state_manager.set_state("menu", use_fade=True)

    def run(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_game()
            
            if event.type == pygame.KEYDOWN:
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
                    
        self.renderer.draw_startup(self)