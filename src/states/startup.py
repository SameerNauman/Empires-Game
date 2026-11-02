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

        # Setup steps: 0 = Player Faction, 1 = Enemy Faction
        self.step = 0
        
        # Available options lists (factions only for now)
        self.factions = ["Seljuks", "Byzantines"]
        
        # Continuous Scroll & Lerp variables
        self.target_scroll_pos = 0.0
        self.scroll_pos = 0.0
        self.slot_width = 320

        # Stored choices (defaulting colors since color selection is removed for now)
        self.player_faction = None
        self.enemy_faction = None
        self.player_color = "blue"
        self.enemy_color = "red"

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def confirm_selection(self):
        current_len = len(self.factions)
        settled_index = int(round(self.target_scroll_pos)) % current_len
        selected_value = self.factions[settled_index].lower()

        if self.step == 0:
            self.player_faction = selected_value
            self.step = 1
            self.target_scroll_pos = 0.0
            self.scroll_pos = 0.0
        elif self.step == 1:
            self.enemy_faction = selected_value
            # All selections complete! Launch gameplay state
            self.game_state_manager.set_state(
                "gameplay state", 
                use_fade=True,
                player_faction=self.player_faction,
                enemy_faction=self.enemy_faction,
                player_color=self.player_color,
                enemy_color=self.enemy_color
            )

    def go_back(self):
        if self.step > 0:
            self.step -= 1
            self.target_scroll_pos = 0.0
            self.scroll_pos = 0.0
        else:
            self.game_state_manager.set_state("menu", use_fade=True)

    def run(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_game()
            
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_a, pygame.K_LEFT]:
                    self.target_scroll_pos -= 1.0
                elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                    self.target_scroll_pos += 1.0
                elif event.key == pygame.K_LSHIFT:
                    self.confirm_selection()
                elif event.key == pygame.K_ESCAPE:
                    self.go_back()

        self.renderer.draw_startup(self)