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

        self.game_state_manager = GameStateManager("menu")
        self.menu = Menu(self.screen, self.game_state_manager)
        self.game_over = GameOver(self.screen, self.game_state_manager, None)
        self.gameplay_state = GameplayState(self.screen, self.game_state_manager)

        self.states = {"gameplay state": self.gameplay_state, "menu": self.menu, "game over": self.game_over}    
    
    def run(self):
        while self.gameplay_state.running:
            # Gather ALL events here
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.gameplay_state.running = False
                elif event.type == pygame.VIDEORESIZE:
                    new_width, new_height = event.size
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    for state in self.states.values():
                        if hasattr(state, "resize"):
                            state.resize(new_width, new_height)

            # Pass the events list to the current state
            self.states[self.game_state_manager.get_state()].run(events)
            
            pygame.display.flip()
            self.clock.tick(60)

class GameStateManager():
    def __init__(self, current_state):
        self.current_state = current_state
    
    def get_state(self):
        return self.current_state
    
    def set_state(self, state):
        self.current_state = state

if __name__ == "__main__":
    main = Main()
    main.run()