import pygame, sys
from message_box import MessageBox
from pop_up_menu import PopupMenu
from config import *

class Menu():
    def __init__(self, screen, game_state_manager):
        self.display = screen
        w, h = screen.get_size()
        self.game_state_manager = game_state_manager

        self.font = pygame.font.SysFont("Times New Roman", 40)

        # Title
        self.title_text = self.font.render("Faith & Fury", True, "#C0C0C0")
        self.title = pygame.Rect(0, 0, 300, 100)
        self.title.center = ((w // 2), (h // 8))

        self.open_controls_menu = False

        # UI elements
        self.load_ui_elements()

        self.message_box = MessageBox(self.display, w, h, self.ui_elements["message_box"])
        self.error_message = True

        self.popup_menu = PopupMenu(
            [], {}, 0, 0, self.ui_elements, self.message_box, 
            sprite_key="popup_menu"
        )

    # Loads the sprites for the UI elements
    def load_ui_elements(self):
            self.ui_elements = {}
            for element_name, data in UI_ELEMENTS.items():
                # Check if it's a dictionary (like your popup_menu)
                if isinstance(data, dict):
                    self.ui_elements[element_name] = {}
                    for state, filename in data.items():
                        full_path = os.path.join(UI_ELEMENTS_PATH, filename)
                        self.ui_elements[element_name][state] = pygame.image.load(full_path).convert_alpha()
                else:
                    # It's a regular string (like message_box)
                    full_path = os.path.join(UI_ELEMENTS_PATH, data)
                    self.ui_elements[element_name] = pygame.image.load(full_path).convert_alpha()

    def main_options(self):
        if self.popup_menu.is_open: # Prevent opening it 60 times a second
            return

        options = ["Start", "Controls", "Quit"]
        actions = {
            "Start": lambda: self.game_state_manager.set_state("gameplay state"),
            "Controls": lambda: self.set_control_menu(active=True),
            "Quit": lambda: self.quit_game()
        }

        self.popup_menu.open(options, actions)

    def set_control_menu(self, active):
        self.open_controls_menu = active

        if active:
            options = ["Main Menu", "Quit"]
            actions = {
                "Main Menu": lambda: self.set_control_menu(active=False),
                "Quit": self.quit_game
            }
            self.popup_menu.is_open = False 
            self.popup_menu.open(options, actions)
        else:
            self.popup_menu.is_open = False
            self.main_options()
    
    def draw_controls_menu(self, width, height):

        # Sprites
        awsd_sprite = self.ui_elements.get("awsd")
        awsd_rect = awsd_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 3.5))
        
        arrows_sprite = self.ui_elements.get("arrows")
        arrows_rect = arrows_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 7.5))

        shift_sprite = self.ui_elements.get("shift")
        shift_rect = shift_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 11))

        tab_sprite = self.ui_elements.get("tab")
        tab_rect = tab_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 14))

        # Text
        controls_text = self.font.render("Controls", True, "#C0C0C0")
        controls = pygame.Rect(0, 0, 300, 100)
        controls.center = ((width // 8), (height // 16))
        controls_rect = controls_text.get_rect(center=controls.center)

        awsd_text = self.font.render("Movement", True, "#C0C0C0")
        awsd_text_rect = ((width // 8) * 4.5, (height // 8) * 2.5)

        shift_text = self.font.render("Selection", True, "#C0C0C0")
        shift_text_rect = ((width // 8) * 4.5, (height // 16) * 10.5)

        tab_text = self.font.render("Cycle", True, "#C0C0C0")
        tab_text_rect = ((width // 8) * 4.5, (height // 16) * 13.5)

        # Display Sprites
        self.display.blit(awsd_sprite, awsd_rect)
        self.display.blit(arrows_sprite, arrows_rect)
        self.display.blit(shift_sprite, shift_rect)
        self.display.blit(tab_sprite, tab_rect)
        
        # Display Text
        self.display.blit(controls_text, controls_rect)
        self.display.blit(awsd_text, awsd_text_rect)
        self.display.blit(shift_text, shift_text_rect)
        self.display.blit(tab_text, tab_text_rect)

    def quit_game(self):
        pygame.quit()
        sys.exit()
    
    def resize(self, w, h):
        self.screen = pygame.display.get_surface()

        self.title.center = ((w // 2), (h // 8))

        self.popup_menu.resize(w, h)

    def draw(self):
        w, h = self.display.get_size()

        # Background
        self.display.fill("#000035")
        
        # Selection
        if not self.popup_menu.is_open and not self.open_controls_menu:
            self.main_options()

        # Controls menu
        if self.open_controls_menu:
            self.draw_controls_menu(w, h)
        else:
            # Title
            title_rect = self.title_text.get_rect(center=self.title.center)
            self.display.blit(self.title_text, title_rect)

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

        self.draw()
        
        self.popup_menu.draw(self.display)