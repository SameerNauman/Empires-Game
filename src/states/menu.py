import pygame, sys
from message_box import MessageBox
from pop_up_menu import PopupMenu
from animated_sprite import AnimatedSprite
from config import *

class Menu():
    def __init__(self, screen, game_state_manager):
        self.display = screen
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        self.game_state_manager = game_state_manager

        self.font = pygame.font.SysFont("Times New Roman", 60)

        # Title
        self.title_text = self.font.render("Faith & Fury", True, "#C0C0C0")
        self.title = pygame.Rect(0, 0, 300, 100)
        self.title.center = ((w // 2), (h // 8))

        self.open_controls_menu = False

        # Fade Screen
        self.fade_alpha = 0
        self.fade_speed = 8  # Speed of the fade
        self.is_fading = False
        self.fade_direction = 1 # 1 for fading to black, -1 for fading to transparent
        self.next_menu_state = None 
        self.fade_surface = pygame.Surface((w, h))
        self.fade_surface.fill((0, 0, 0))

        # UI elements
        self.load_ui_elements()

        # Screens
        self.load_animated_screens()

        self.message_box = MessageBox(self.display, w, h, self.ui_elements["message_box"])
        self.error_message = True

        self.popup_menu = PopupMenu(
            [], {}, 0, 0, self.ui_elements, self.message_box, 
            sprite_key="popup_menu", state="menu"
        )

        # Main Menu
        self.main_options()

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
    
    def load_animated_screens(self):
        self.animated_sprites = {}

        for name, data in ANIMATED_SCREENS.items():
            filename = data[0]
            full_path = os.path.join(SCREENS_PATH, filename)

            rows = data[3]
            cols = data[4]
            
            self.animated_sprites[name] = AnimatedSprite(full_path, rows, cols)

    def display_animated_screens(self, name):
        anim = self.animated_sprites.get(name)
        if not anim: return
        
        w, h = self.display.get_size()
        sprite = anim.get_current_frame()

        if sprite:
            anim.update() 
            
            rect = sprite.get_rect(topleft=(0, 0))
            self.display.blit(sprite, rect)

    def draw_text_with_shadow(self, text, color, position, offset=(2, 2)):
        shadow_surf = self.font.render(text, True, (20, 20, 20))
        shadow_pos = (position[0] + offset[0], position[1] + offset[1])
        self.display.blit(shadow_surf, shadow_pos)

        main_surf = self.font.render(text, True, color)
        self.display.blit(main_surf, position)
        
    def main_options(self, force=False):
        if self.popup_menu.is_open and not force: 
            return

        options = ["New Game", "Controls", "Quit"]
        actions = {
            "New Game": lambda: self.game_state_manager.set_state("gameplay state"),
            "Controls": lambda: self.set_control_menu(active=True),
            "Quit": lambda: self.quit_game()
        }

        self.popup_menu.open(options, actions)

    def set_control_menu(self, active):
        self.is_fading = True
        self.fade_direction = 1
        self.next_menu_state = active

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
        self.draw_text_with_shadow("Controls", "#C0C0C0", ((width // 8) - 100, (height // 16)))
        self.draw_text_with_shadow("Movement", "#C0C0C0", ((width // 8) * 4.5, (height // 8) * 2.5))
        self.draw_text_with_shadow("Selection", "#C0C0C0", ((width // 8) * 4.5, (height // 16) * 10.5))
        self.draw_text_with_shadow("Cycle", "#C0C0C0", ((width // 8) * 4.5, (height // 16) * 13.5))

        # Display Sprites
        self.display.blit(awsd_sprite, awsd_rect)
        self.display.blit(arrows_sprite, arrows_rect)
        self.display.blit(shift_sprite, shift_rect)
        self.display.blit(tab_sprite, tab_rect)

    def quit_game(self):
        pygame.quit()
        sys.exit()
    
    # def resize(self, w, h):
    #     self.screen = pygame.display.get_surface()

    #     self.title.center = ((w // 2), (h // 8))

    #     self.popup_menu.resize(w, h)

    def draw(self):
        w, h = self.display.get_size()

        self.display.fill((0, 0, 0))

        # Background
        # title_sprite = self.ui_elements.get("title")
        # self.display.blit(title_sprite, (0, 0))

        self.display_animated_screens("title")

        # Controls menu
        if self.open_controls_menu:
            self.draw_controls_menu(w, h)
        else:
            # Title
            title_rect = self.title_text.get_rect(center=self.title.center)
            self.draw_text_with_shadow("Faith & Fury", "#C0C0C0", title_rect)
        
        if self.popup_menu.is_open:
            self.popup_menu.draw(self.display)

        if self.is_fading:
            self.fade_alpha += (self.fade_speed * self.fade_direction)
            
            # Logic when fully black
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.fade_direction = -1 # Start fading back in

                self.popup_menu.is_open = False
                
                # Switch the actual content here while screen is black
                self.open_controls_menu = self.next_menu_state
                # self.popup_menu.is_open = False # Reset popup for fresh state
                
                if self.open_controls_menu:
                    options = ["Main Menu", "Quit"]
                    actions = {"Main Menu": lambda: self.set_control_menu(active=False), "Quit": self.quit_game}
                    self.popup_menu.open(options, actions)
                else:
                    self.main_options(force=True)

            # Logic when fade back in is finished
            elif self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.is_fading = False

            self.fade_surface.set_alpha(self.fade_alpha)
            self.display.blit(self.fade_surface, (0, 0))

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
        