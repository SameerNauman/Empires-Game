import pygame
import sys
from states.gameplay_state import GameplayState
from states.menu import Menu
from states.game_over import GameOver
from config import *

# make sure enemies gather resources.

class Main():
    def __init__(self):
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.virtual_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("Faith & Fury")
        self.clock = pygame.time.Clock()
        self.fullscreen = False

        self.game_state_manager = GameStateManager("menu", self.virtual_surface)

        self.menu = Menu(self.virtual_surface, self.game_state_manager)
        self.game_over = GameOver(self.virtual_surface, self.game_state_manager, None)
        self.gameplay_state = GameplayState(self.virtual_surface, self.game_state_manager)

        self.states = {
            "gameplay state": self.gameplay_state,
            "menu": self.menu,
            "game over": self.game_over
        }

        self.target_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

    def calculate_aspect_ratio(self, new_width, new_height):
        target_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        window_ratio = new_width / new_height

        if window_ratio > target_ratio:
            scale_height = new_height
            scale_width = int(new_height * target_ratio)
        else:
            scale_width = new_width
            scale_height = int(new_width / target_ratio)

        x = (new_width - scale_width) // 2
        y = (new_height - scale_height) // 2
        self.target_rect = pygame.Rect(x, y, scale_width, scale_height)    
    
    def run(self):
        while self.gameplay_state.running:
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.gameplay_state.running = False
                
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    
                    w, h = self.screen.get_size()
                    self.calculate_aspect_ratio(w, h)

                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    new_width, new_height = event.size
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    self.calculate_aspect_ratio(new_width, new_height)

            current_events = [] if self.game_state_manager.is_transitioning else events
            self.states[self.game_state_manager.get_state()].run(current_events)
            self.game_state_manager.update_transition()

            self.screen.fill((0, 0, 0))
            scaled_surface = pygame.transform.smoothscale(self.virtual_surface, (self.target_rect.width, self.target_rect.height))
            self.screen.blit(scaled_surface, (self.target_rect.x, self.target_rect.y))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

class GameStateManager():
    def __init__(self, current_state, virtual_surface):
        self.current_state = current_state

        self.screen = virtual_surface
        
        # Transition Variables
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 0
        self.fade_speed = 8
        self.fade_direction = 1  # 1 for out (to black), -1 for in (to transparent)
        self.is_transitioning = False
        self.pending_state = None
    
    def get_state(self):
        return self.current_state
    
    def set_state(self, state, use_fade=True):
        if use_fade:
            self.is_transitioning = True
            self.fade_direction = 1
            self.pending_state = state
        else:
            self.current_state = state

    def update_transition(self):
        if not self.is_transitioning:
            return

        self.fade_alpha += (self.fade_speed * self.fade_direction)

        if self.fade_alpha >= 255 and self.fade_direction == 1:
            self.fade_alpha = 255
            self.current_state = self.pending_state
            self.fade_direction = -1
            self.screen.fill((0, 0, 0)) 
        
        elif self.fade_alpha <= 0 and self.fade_direction == -1:
            self.fade_alpha = 0
            self.is_transitioning = False

        self.fade_surface.set_alpha(self.fade_alpha)
        self.screen.blit(self.fade_surface, (0, 0))

if __name__ == "__main__":
    main = Main()
    main.run()