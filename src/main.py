import pygame
import sys
from states.gameplay_state import GameplayState
from states.menu import Menu
from states.startup import StartUp
from states.game_over import GameOver
from config import *

# make sure enemies gather resources.

class Main():
    def __init__(self):
        # Initialize pygame
        pygame.init()
        # Initialize screen and virtual surface. Virtual surface is used for scaling to maintain aspect ratio.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.virtual_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("Faith & Fury")
        self.clock = pygame.time.Clock()
        self.fullscreen = False

        # initialize game state manager and states. Game state manager handles transitions between states and keeps track of the 
        # current state. Menu state is the initial state, so it is passed to the game state manager as the current state.
        self.game_state_manager = GameStateManager("menu", self.virtual_surface)

        # Pass game state manager to each state so they can change the current state when needed. Menu state is the main menu, it 
        # shows the controls, and allows the player to start the game. Gameplay state is the main game, it handles the game logic 
        # and rendering. Game over state is shown when the player loses, it shows the score and allows the player to restart or go
        # back to the menu. Start up state is shown when the game is first launched, it shows a splash screen and then transitions 
        # to the menu state.
        self.menu = Menu(self.virtual_surface, self.game_state_manager)
        self.game_over = GameOver(self.virtual_surface, self.game_state_manager, None)
        self.gameplay_state = GameplayState(self.virtual_surface, self.game_state_manager)
        self.startup = StartUp(self.virtual_surface, self.game_state_manager)

        # Define a dictionary to hold the states and their corresponding objects. This allows for easy access to the states by name.
        self.states = {
            "gameplay state": self.gameplay_state,
            "menu": self.menu,
            "start up": self.startup,
            "game over": self.game_over
        }

        # Set the states reference in the game state manager to the states dictionary. This allows the game state manager to access 
        # the states by name.
        self.game_state_manager.states_ref = self.states

        # Set the initial target rectangle to the full screen size. This will be used to scale the virtual surface to fit the window while 
        # maintaining the aspect ratio. 
        self.target_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Calculate the aspect ratio of the window and adjust the target rectangle accordingly. This ensures that the game maintains its 
    # aspect ratio when the window is resized or when switching between fullscreen and windowed mode.
    def calculate_aspect_ratio(self, new_width, new_height):
        target_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        window_ratio = new_width / new_height

        if window_ratio > target_ratio:
            scale_height = new_height
            scale_width = int(new_height * target_ratio)
        else:
            scale_width = new_width
            scale_height = int(new_width / target_ratio)

        # Center the scaled surface within the window by calculating the x and y offsets. This ensures that the game is always 
        # centered in the window.
        x = (new_width - scale_width) // 2
        y = (new_height - scale_height) // 2
        # Update the target rectangle with the new dimensions and position. This rectangle will be used to scale the virtual surface
        self.target_rect = pygame.Rect(x, y, scale_width, scale_height)    

    # Main game loop. This loop handles events, updates the current state, and renders the game to the screen. It also handles 
    # transitions between states
    def run(self):
        while self.gameplay_state.running:
            # Handle events. Events include user input (keyboard, mouse), window events (resize, close), and other system events.
            # The events are passed to the current state for handling.
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

                # Handle window resize events. If the window is resized and the game is not in fullscreen mode, update the screen size and
                # recalculate the aspect ratio to maintain the game's aspect ratio.
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    new_width, new_height = event.size
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    self.calculate_aspect_ratio(new_width, new_height)

            # Update the current state. If the game is transitioning between states, pass an empty list of events to the current
            # state to prevent it from processing any events during the transition. Otherwise, pass the actual events to the current state
            current_events = [] if self.game_state_manager.is_transitioning else events
            self.states[self.game_state_manager.get_state()].run(current_events)
            self.game_state_manager.update_transition()

            # Render the current state to the virtual surface. The virtual surface is then scaled to fit the window while maintaining the
            # aspect ratio. The scaled surface is then blitted to the screen and the display is updated. The clock is ticked to limit the
            # frame rate to 60 frames per second.
            self.screen.fill((0, 0, 0))
            scaled_surface = pygame.transform.smoothscale(self.virtual_surface, (self.target_rect.width, self.target_rect.height))
            self.screen.blit(scaled_surface, (self.target_rect.x, self.target_rect.y))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# GameStateManager class handles the current state of the game and transitions between states. It manages the fade effect during 
# transitions and allows for passing additional arguments to the new state.
class GameStateManager():
    def __init__(self, current_state, virtual_surface):
        self.current_state = current_state
        self.screen = virtual_surface

        # Reference to the states dictionary, which holds the state names and their corresponding objects. This allows the game state
        # manager to access the states by name and call their methods during transitions.
        self.states_ref = None

        self.player_faction = None
        
        # Transition Variables.
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 0
        # Fade speed controls how quickly the fade effect occurs. A higher value results in a faster fade.
        self.fade_speed = 8
        self.fade_direction = 1  # 1 for out (to black), -1 for in (to transparent)
        # is_transitioning indicates whether a transition is currently in progress. If True, the game is in the process of fading out and
        # then fading in to the new state. pending_state holds the name of the state to transition to, and pending_kwargs holds any
        # additional arguments that need to be passed to the new state during the transition.
        self.is_transitioning = False
        self.pending_state = None
        self.pending_kwargs = {}

    # Returns the name of the current state. This method is used by the main game loop to determine which state to update and render.
    def get_state(self):
        return self.current_state

    # Sets the current state to the specified state. If use_fade is True, the transition will include a fade effect. Additional keyword
    # arguments can be passed to the new state during the transition. These arguments are stored in pending_kwargs and will be
    # passed to the new state's enter method when the transition is complete.
    def set_state(self, state, use_fade=True, **kwargs):
        if use_fade:
            self.is_transitioning = True
            self.fade_direction = 1
            self.pending_state = state
            self.pending_kwargs = kwargs 
        else:
            self.current_state = state
            self.pending_kwargs = {}

    # Updates the fade effect during a state transition. This method is called in the main game loop to gradually change the alpha
    # value of the fade surface, creating a fade-out and fade-in effect. When the fade-out is complete, the current state is updated
    # to the pending state, and any additional arguments are passed to the new state's enter method. When the fade-in is complete,
    # the transition is finished, and the game resumes normal operation.
    def update_transition(self):
        if not self.is_transitioning:
            return

        # Update the fade alpha value based on the fade speed and direction.
        self.fade_alpha += (self.fade_speed * self.fade_direction)

        # Check if the fade-out is complete (alpha >= 255) and switch to the pending state. If the fade-in is complete (alpha <= 0),
        # reset the transition state and allow the game to continue.
        if self.fade_alpha >= 255 and self.fade_direction == 1:
            self.fade_alpha = 255
            self.current_state = self.pending_state
            self.fade_direction = -1

            # After switching to the new state, check if the new state object exists in the states reference. If it does, and if there are
            # any pending keyword arguments, pass them to the new state's enter method. This allows for dynamic configuration of the new
            # state based on the context of the transition (e.g., passing player faction or enemy faction information).
            target_state_obj = self.states_ref.get(self.current_state) if self.states_ref else None
            if target_state_obj:
                if self.pending_kwargs:
                    if hasattr(target_state_obj, "player_faction"):
                        target_state_obj.player_faction = self.pending_kwargs.get("player_faction")
                    if hasattr(target_state_obj, "enemy_faction"):
                        target_state_obj.enemy_faction = self.pending_kwargs.get("enemy_faction")

                if hasattr(target_state_obj, "enter"):
                    target_state_obj.enter(**self.pending_kwargs)
            
            self.pending_kwargs = {}
        
        elif self.fade_alpha <= 0 and self.fade_direction == -1:
            self.fade_alpha = 0
            self.is_transitioning = False

        self.fade_surface.set_alpha(self.fade_alpha)
        self.screen.blit(self.fade_surface, (0, 0))

if __name__ == "__main__":
    main = Main()
    main.run()