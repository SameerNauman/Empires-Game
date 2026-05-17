import pygame, sys
from message_box import MessageBox
from pop_up_menu import PopupMenu
from animated_sprite import AnimatedSprite
from config import *

class StartUp():
    def __init__(self, screen, game_state_manager):
        self.display = screen
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        self.game_state_manager = game_state_manager

        self.font = pygame.font.SysFont("Times New Roman", 60)

        self.pending_faction_choice = None
        self.selection_phase = "player"
        self.player_faction = None
        self.enemy_faction = None

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

        self.faction_selection()
    
    # Loads the sprites for the UI elements
    def load_ui_elements(self):
        self.ui_elements = {}
        for element_name, data in UI_ELEMENTS.items():
            if isinstance(data, dict):
                self.ui_elements[element_name] = {}
                for sub_key, filename in data.items():
                    # This correctly maps self.ui_elements["banner"]["seljuks"] = image_surface
                    if element_name == "banner":
                        full_path = os.path.join(UI_ELEMENTS_PATH, filename)
                    else:
                        full_path = os.path.join(UI_ELEMENTS_PATH, filename)
                        
                    self.ui_elements[element_name][sub_key] = pygame.image.load(full_path).convert_alpha()
            else:
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

    def faction_selection(self):
        if self.popup_menu.is_open: 
            return

        options = ["Seljuks", "Byzantines", "Quit"]
        actions = {
            "Seljuks": lambda: self.set_faction("seljuks"),
            "Byzantines": lambda: self.set_faction("byzantines"),
            "Quit": lambda: self.quit_game()
        }

        self.popup_menu.open(options, actions)
    
    def enemy_faction_selection(self):
        if self.popup_menu.is_open:
            return

        options = ["Seljuks", "Byzantines", "Back"]
        actions = {
            "Seljuks": lambda: self.set_faction("seljuks"),
            "Byzantines": lambda: self.set_faction("byzantines"),
            "Back": lambda: self.set_faction("back")  # Allows backing out to the player selection phase
        }

        self.popup_menu.open(options, actions)

    def set_faction(self, faction):
        # Cleanly shut down old menu properties to accept new items safely
        self.popup_menu.close()
        self.popup_menu.is_open = False

        if self.selection_phase == "player":
            self.player_faction = faction
            self.selection_phase = "enemy"
            self.enemy_faction_selection()

        elif self.selection_phase == "enemy":
            if faction == "back":
                self.selection_phase = "player"
                self.player_faction = None
                self.faction_selection()
            else:
                self.enemy_faction = faction
                self.game_state_manager.set_state(
                    "gameplay state", 
                    use_fade=True,
                    player_faction=self.player_faction,
                    enemy_faction=self.enemy_faction
                )

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def draw(self):
        w, h = self.display.get_size()
        self.display.fill((0, 0, 0))
        self.display_animated_screens("title")

        if self.selection_phase == "player":
            self.draw_text_with_shadow("Select Player Faction", "#C0C0C0", ((w // 8) - 100, (h // 16)))
        elif self.selection_phase == "enemy":
            self.draw_text_with_shadow("Select Enemy Faction", "#C0C0C0", ((w // 8) - 100, (h // 16)))

        if self.popup_menu.is_open:
            self.popup_menu.draw(self.display)

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