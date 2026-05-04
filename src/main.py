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
        pygame.display.set_caption("Faith & Fury")
        self.clock = pygame.time.Clock()

        self.game_state_manager = GameStateManager("menu", self.screen)

        self.menu = Menu(self.screen, self.game_state_manager)
        self.game_over = GameOver(self.screen, self.game_state_manager, None)
        self.gameplay_state = GameplayState(self.screen, self.game_state_manager)

        self.states = {
            "gameplay state": self.gameplay_state,
            "menu": self.menu,
            "game over": self.game_over
        }    
    
    def run(self):
        while self.gameplay_state.running:
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.gameplay_state.running = False
                elif event.type == pygame.VIDEORESIZE:
                    new_width, new_height = event.size
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    self.game_state_manager.fade_surface = pygame.Surface((new_width, new_height))
                    self.game_state_manager.fade_surface.fill((0, 0, 0))
                    for state in self.states.values():
                        if hasattr(state, "resize"):
                            state.resize(new_width, new_height)

            current_events = [] if self.game_state_manager.is_transitioning else events
            self.states[self.game_state_manager.get_state()].run(current_events)

            self.game_state_manager.update_transition()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

class GameStateManager():
    def __init__(self, current_state, screen):
        self.current_state = current_state

        self.screen = screen
        
        # Transition Variables
        self.fade_surface = pygame.Surface(screen.get_size())
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