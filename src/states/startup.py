import pygame, sys, os
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
        self.player_color = None
        self.enemy_faction = None
        self.enemy_color = None

        self.load_ui_elements()

        self.color_icons = {}
        self.load_color_icons()

        self.load_animated_screens()

        self.message_box = MessageBox(self.display, w, h, self.ui_elements["message_box"])
        self.error_message = True

        self.popup_menu = PopupMenu(
            [], {}, 0, 0, self.ui_elements, self.message_box, 
            sprite_key="popup_menu", state="menu"
        )

        self.building_menu = PopupMenu(
            [], {}, 0, 0, self.ui_elements, self.message_box, 
            sprite_key="building_menu", side="right"
        )

        self.faction_selection()
    
    def load_ui_elements(self):
        self.ui_elements = {}
        for element_name, data in UI_ELEMENTS.items():
            if isinstance(data, dict):
                self.ui_elements[element_name] = {}
                for sub_key, filename in data.items():
                    if element_name == "banner":
                        full_path = os.path.join(UI_ELEMENTS_PATH, filename)
                    else:
                        full_path = os.path.join(UI_ELEMENTS_PATH, filename)
                        
                    self.ui_elements[element_name][sub_key] = pygame.image.load(full_path).convert_alpha()
            else:
                full_path = os.path.join(UI_ELEMENTS_PATH, data)
                self.ui_elements[element_name] = pygame.image.load(full_path).convert_alpha()

    def load_color_icons(self):
        for color_name, filename in COLOR_ICONS.items():
            full_path = os.path.join(COLOR_ICONS_PATH, filename)
            try:
                sprite = pygame.image.load(full_path).convert_alpha()
                self.color_icons[color_name] = sprite
            except pygame.error as e:
                print(f"[UI ERROR] Unable to load color asset texture {filename} from path {COLOR_ICONS_PATH}: {e}")

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
            "Back": lambda: self.set_faction("back")  
        }

        self.popup_menu.open(options, actions)

    def set_faction(self, faction):
        self.popup_menu.close()
        self.popup_menu.is_open = False

        if self.selection_phase == "player":
            if faction == "quit":
                self.quit_game()
            else:
                self.player_faction = faction
                self.color_selection()

        elif self.selection_phase == "enemy":
            if faction == "back":
                self.selection_phase = "player"
                self.player_faction = None
                self.player_color = None
                self.faction_selection()
            else:
                self.enemy_faction = faction
                self.enemy_color_selection()

    def color_selection(self):
        if self.building_menu.is_open: 
            return
        
        options = ["Blue", "Red", "Green", "Yellow", "Back"]
        
        actions = {
            "Blue": lambda: self.set_color("blue"),
            "Red": lambda: self.set_color("red"),
            "Green": lambda: self.set_color("green"),
            "Yellow": lambda: self.set_color("yellow"),
            "Back": lambda: self.set_color("back")
        }

        icon_mapping = {
            "Blue": self.color_icons.get("blue"),
            "Red": self.color_icons.get("red"),
            "Green": self.color_icons.get("green"),
            "Yellow": self.color_icons.get("yellow"),
            "Back": None
        }

        self.building_menu.sprites["building_icons"] = icon_mapping
        self.building_menu.sprite_key = "building_menu" 

        self.popup_menu.close()
        self.building_menu.open(options, actions)

    def enemy_color_selection(self):
        if self.building_menu.is_open:
            return

        options = ["Blue", "Red", "Green", "Yellow", "Back"]
        actions = {
            "Blue": lambda: self.set_color("blue"),
            "Red": lambda: self.set_color("red"),
            "Green": lambda: self.set_color("green"),
            "Yellow": lambda: self.set_color("yellow"),
            "Back": lambda: self.set_color("back")
        }

        icon_mapping = {
            "Blue": self.color_icons.get("blue"),
            "Red": self.color_icons.get("red"),
            "Green": self.color_icons.get("green"),
            "Yellow": self.color_icons.get("yellow"),
            "Back": None
        }

        self.building_menu.sprites["building_icons"] = icon_mapping
        
        self.building_menu.sprite_key = "building_menu"

        self.popup_menu.close()
        self.building_menu.open(options, actions)

    def set_color(self, color):
        self.building_menu.close()
        self.building_menu.is_open = False

        if self.selection_phase == "player":
            if color == "back":
                self.player_faction = None
                self.faction_selection()
            else:
                self.player_color = color
                self.selection_phase = "enemy"
                self.enemy_faction_selection()

        elif self.selection_phase == "enemy":
            if color == "back":
                self.enemy_faction = None
                self.enemy_faction_selection()
            else:
                self.enemy_color = color
                self.game_state_manager.set_state(
                    "gameplay state", 
                    use_fade=True,
                    player_faction=self.player_faction,
                    enemy_faction=self.enemy_faction,
                    player_color=self.player_color,
                    enemy_color=self.enemy_color
                )

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def draw(self):
        w, h = self.display.get_size()
        self.display.fill((0, 0, 0))
        self.display_animated_screens("title")

        if self.selection_phase == "player":
            if not self.player_faction:
                self.draw_text_with_shadow("Select Player Faction", "#C0C0C0", ((w // 8) - 100, (h // 16)))
            else:
                self.draw_text_with_shadow("Select Player Color", "#C0C0C0", ((w // 8) - 100, (h // 16)))
        elif self.selection_phase == "enemy":
            if not self.enemy_faction:
                self.draw_text_with_shadow("Select Enemy Faction", "#C0C0C0", ((w // 8) - 100, (h // 16)))
            else:
                self.draw_text_with_shadow("Select Enemy Color", "#C0C0C0", ((w // 8) - 100, (h // 16)))

        if self.popup_menu.is_open:
            self.popup_menu.draw(self.display)
            
        if self.building_menu.is_open:
            self.building_menu.draw(self.display)

    def run(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                active_menu = self.popup_menu if self.popup_menu.is_open else self.building_menu
                if active_menu.is_open:
                    if event.key in [pygame.K_w, pygame.K_UP]:
                        active_menu.move_selection(-1)
                    elif event.key in [pygame.K_s, pygame.K_DOWN]:
                        active_menu.move_selection(1)
                    elif event.key == pygame.K_LSHIFT:
                        active_menu.select()
                    return 

        self.draw()