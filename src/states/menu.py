import pygame, sys
from message_box import MessageBox
from pop_up_menu import PopupMenu
from animated_sprite import AnimatedSprite
from fade_manager import FadeManager
from renderer import Renderer
from config import *

class Menu():
    def __init__(self, screen, game_state_manager, asset_manager):
        # Initialize the Menu class with the display surface and game state manager
        self.display = screen
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        self.game_state_manager = game_state_manager
        self.assets = asset_manager
        self.renderer = Renderer(self.display, self.assets)

        self.font = pygame.font.SysFont("Times New Roman", 60)

        # Title positioned at the top center of the screen
        self.title_text = self.font.render("Faith & Fury", True, "#C0C0C0")
        self.title = pygame.Rect(0, 0, 300, 100)
        self.title.center = ((w // 2), (h // 8))

        # Controls menu state. When True, the controls menu is displayed; when False, the main menu is displayed.
        self.open_controls_menu = False
        self.next_menu_state = None

        # Fade Screen transition
        self.fade_manager = FadeManager()

        self.message_box = MessageBox(self.display, w, h, self.assets.ui_elements["message_box"])
        self.error_message = True

        self.popup_menu = PopupMenu(
            [], {}, 0, 0, self.assets.ui_elements, self.message_box, 
            sprite_key="popup_menu", state="menu"
        )

        # Main Menu
        self.main_options()

    # Displays the main menu options and handles user interactions. If the popup menu is already open and 'force' is False, 
    # it does nothing. Otherwise, it opens the popup menu with the specified options and their corresponding actions.    
    def main_options(self, force=False):
        if self.popup_menu.is_open and not force: 
            return

        options = ["New Game", "Controls", "Quit"]
        actions = {
            "New Game": lambda: self.game_state_manager.set_state("start up"),
            "Controls": lambda: self.set_control_menu(active=True),
            "Quit": lambda: self.quit_game()
        }

        self.popup_menu.open(options, actions)

    # Sets the state of the controls menu. If 'active' is True, the controls menu will be displayed; if False, the main 
    # menu will be displayed.
    def set_control_menu(self, active):
        self.next_menu_state = active
        self.fade_manager.start_fade()

    # Quits the game by calling pygame.quit() and sys.exit() to close the application.
    def quit_game(self):
        pygame.quit()
        sys.exit()

    # Handles user input events. It processes quit events, key presses for navigating the popup menu, and selection actions.
    def run(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.popup_menu.is_open:
                    if event.key in [pygame.K_w, pygame.K_UP]:
                        self.popup_menu.move_selection(-1)
                    elif event.key in [pygame.K_s, pygame.K_DOWN]:
                        self.popup_menu.move_selection(1)
                    elif event.key == pygame.K_LSHIFT:
                        self.popup_menu.select()
                    return # Block all other inputs

        self.renderer.draw_menu(self)

        # Update and draw the fade transition
        fade_event = self.fade_manager.update()
        self.fade_manager.draw(self.display)

        # When the screen hits peak blackness, swap the menu content safely
        if fade_event == "PEAK_BLACK":
            self.popup_menu.is_open = False
            self.open_controls_menu = self.next_menu_state
            
            if self.open_controls_menu:
                options = ["Main Menu", "Quit"]
                actions = {"Main Menu": lambda: self.set_control_menu(active=False), "Quit": self.quit_game}
                self.popup_menu.open(options, actions)
            else:
                self.main_options(force=True)        