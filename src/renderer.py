import math
import pygame
from animated_sprite import AnimatedSprite
from fade_manager import FadeManager
from config import *

class Renderer:
    def __init__(self, screen, asset_manager):
        self.screen = screen
        self.assets = asset_manager
        self.fade_manager = FadeManager()

        self.font = pygame.font.SysFont("Times New Roman", 50)
        self.small_font = pygame.font.SysFont("Times New Roman", 35)

    # Shadow effect for title screens
    def draw_text_with_shadow(self, text, color, position, offset=(2, 2), font=None, surface=None):
        f = font if font else self.font
        surf = surface if surface else self.screen
        
        shadow_surf = f.render(text, True, (20, 20, 20))
        shadow_pos = (position[0] + offset[0], position[1] + offset[1])
        surf.blit(shadow_surf, shadow_pos)

        main_surf = f.render(text, True, color)
        surf.blit(main_surf, position)

    # 3-Column Grid Version for Startup Screen
    def draw_startup2(self, startup):
        w, h = self.screen.get_size()
        self.screen.fill((0, 0, 0))

        # Background Animation
        anim = self.assets.animated_sprites.get("title")
        if anim:
            sprite = anim.get_current_frame()
            if sprite:
                anim.update()
                self.screen.blit(sprite, (0, 0))

        # Translucent Dark Backdrop
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        # Header Title
        title = "Player Configuration"
        title_rect = self.font.render(title, True, "#D0D0D0").get_rect(center=(w // 2, int(h * 0.12)))
        self.draw_text_with_shadow(title, "#D0D0D0", title_rect.topleft)

        popup_sprite = self.assets.ui_elements.get("carousel") # Popup/card sprite asset
        
        # 3-Column X Positions
        col1_x = int(w * 0.22)  # Player 1 Column
        col2_x = int(w * 0.50)  # Middle Labels Column
        col3_x = int(w * 0.78)  # Player 2 Column

        header_y = int(h * 0.22)  # Player Headers Row
        row1_y = int(h * 0.32)    # Faction Row
        row2_y = int(h * 0.46)    # Color Row
        row3_y = int(h * 0.60)    # Confirm Button Row
        row4_y = int(h * 0.70)    # Main Menu Button Row

        btn_w, btn_h = 240, 48

        # Player column headers highlighted only when selected.
        p1_active = (startup.selected_col == 0 and startup.selected_row < 2)
        p2_active = (startup.selected_col == 2 and startup.selected_row < 2)

        p1_hdr_color = "#FFD700" if p1_active else "#808080"
        p2_hdr_color = "#FFD700" if p2_active else "#808080"

        p1_lbl = self.small_font.render("PLAYER 1", True, p1_hdr_color)
        p1_rect = p1_lbl.get_rect(center=(col1_x, header_y))
        self.draw_text_with_shadow("PLAYER 1", p1_hdr_color, p1_rect.topleft, font=self.small_font)

        p2_lbl = self.small_font.render("PLAYER 2", True, p2_hdr_color)
        p2_rect = p2_lbl.get_rect(center=(col3_x, header_y))
        self.draw_text_with_shadow("PLAYER 2", p2_hdr_color, p2_rect.topleft, font=self.small_font)

        # Faction and color labels
        labels = [("FACTION", row1_y), ("COLOR", row2_y)]
        for lbl_text, ry in labels:
            lbl_surf = self.small_font.render(lbl_text, True, "#A0A0A0")
            lbl_rect = lbl_surf.get_rect(center=(col2_x, ry))
            self.draw_text_with_shadow(lbl_text, "#A0A0A0", lbl_rect.topleft, font=self.small_font)

        # Selections
        p1_faction_name = startup.factions[startup.p1_faction_idx]
        p2_faction_name = startup.factions[startup.p2_faction_idx]
        p1_color_name = startup.colors[startup.p1_color_idx]
        p2_color_name = startup.colors[startup.p2_color_idx]

        # --- ROW 0: FACTIONS (Col 0: P1, Col 2: P2) ---
        p1_f_rect = pygame.Rect(0, 0, btn_w, btn_h)
        p1_f_rect.center = (col1_x, row1_y)
        p1_f_sel = (startup.selected_row == 0 and startup.selected_col == 0)
        self._draw_borderless_button(p1_faction_name, p1_f_rect, p1_f_sel, startup.is_editing and p1_f_sel, popup_sprite)

        p2_f_rect = pygame.Rect(0, 0, btn_w, btn_h)
        p2_f_rect.center = (col3_x, row1_y)
        p2_f_sel = (startup.selected_row == 0 and startup.selected_col == 2)
        self._draw_borderless_button(p2_faction_name, p2_f_rect, p2_f_sel, startup.is_editing and p2_f_sel, popup_sprite)

        # --- FACTION FLAGS (Rendered in the horizontal gap between buttons and center label) ---
        flag_assets = self.assets.ui_elements.get("flag", {})
        p1_flag_sprite = flag_assets.get(p1_faction_name.lower())
        p2_flag_sprite = flag_assets.get(p2_faction_name.lower())

        # Exact center midpoint between the inner edge of the carousel and the center label column (col2_x)
        p1_flag_x = (p1_f_rect.right + col2_x) // 2
        p2_flag_x = (col2_x + p2_f_rect.left) // 2

        if p1_flag_sprite:
            flag_rect = p1_flag_sprite.get_rect(center=(p1_flag_x, row1_y))
            self.screen.blit(p1_flag_sprite, flag_rect)
        if p2_flag_sprite:
            flag_rect = p2_flag_sprite.get_rect(center=(p2_flag_x, row1_y))
            self.screen.blit(p2_flag_sprite, flag_rect)

        # --- ROW 1: COLORS (Col 0: P1, Col 2: P2) ---
        p1_c_rect = pygame.Rect(0, 0, btn_w, btn_h)
        p1_c_rect.center = (col1_x, row2_y)
        p1_c_sel = (startup.selected_row == 1 and startup.selected_col == 0)
        self._draw_borderless_button(p1_color_name, p1_c_rect, p1_c_sel, startup.is_editing and p1_c_sel, popup_sprite)

        p2_c_rect = pygame.Rect(0, 0, btn_w, btn_h)
        p2_c_rect.center = (col3_x, row2_y)
        p2_c_sel = (startup.selected_row == 1 and startup.selected_col == 2)
        self._draw_borderless_button(p2_color_name, p2_c_rect, p2_c_sel, startup.is_editing and p2_c_sel, popup_sprite)

        # --- COLOR SPRITES ---
        p1_color_sprite = self.assets.ui_elements.get(p1_color_name.lower())
        p2_color_sprite = self.assets.ui_elements.get(p2_color_name.lower())

        p1_c_icon_x = (p1_c_rect.right + col2_x) // 2
        p2_c_icon_x = (col2_x + p2_c_rect.left) // 2

        if p1_color_sprite:
            c_rect = p1_color_sprite.get_rect(center=(p1_c_icon_x, row2_y))
            self.screen.blit(p1_color_sprite, c_rect)
        if p2_color_sprite:
            c_rect = p2_color_sprite.get_rect(center=(p2_c_icon_x, row2_y))
            self.screen.blit(p2_color_sprite, c_rect)

        # --- ROW 2: CONFIRM & START BUTTON ---
        confirm_rect = pygame.Rect(0, 0, 300, 50)
        confirm_rect.center = (w // 2, row3_y)
        is_confirm_sel = (startup.selected_row == 2)
        self._draw_borderless_button("CONFIRM", confirm_rect, is_confirm_sel, False, popup_sprite)

        # --- ROW 3: MAIN MENU BUTTON ---
        menu_rect = pygame.Rect(0, 0, 300, 50)
        menu_rect.center = (w // 2, row4_y)
        is_menu_sel = (startup.selected_row == 3)
        self._draw_borderless_button("MAIN MENU", menu_rect, is_menu_sel, False, popup_sprite)

        # Faction descriptions
        if startup.selected_row == 0:
            active_faction = p1_faction_name if startup.selected_col == 0 else p2_faction_name
            desc_text = startup.faction_descriptions.get(active_faction, "")
            if desc_text:
                max_width = w - 200 
                desc_y = int(h * 0.88)
                self._draw_multiline_text_centered(desc_text, self.small_font, "#D0D0D0", w // 2, desc_y, max_width)

    def _draw_borderless_button(self, text, rect, is_selected, is_editing, popup_sprite):
        if popup_sprite:
            bg_surf = pygame.transform.scale(popup_sprite, (rect.width, rect.height))
            alpha = 250 if is_editing else (180 if is_selected else 110)
            bg_surf.set_alpha(alpha)
            self.screen.blit(bg_surf, rect)
        else:
            pygame.draw.rect(self.screen, (40, 40, 50), rect, border_radius=4)

        text_color = "#FFD700" if is_editing else ("#00FFFF" if is_selected else "#C0C0C0")
        txt_surf = self.small_font.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=rect.center)
        
        self.draw_text_with_shadow(text, text_color, txt_rect.topleft, font=self.small_font)

    def _draw_multiline_text_centered(self, text, font, color, center_x, center_y, max_width):
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        line_height = font.get_linesize()
        total_height = len(lines) * line_height
        start_y = center_y - (total_height // 2)

        for i, line in enumerate(lines):
            line_y = start_y + (i * line_height)
            surf = font.render(line, True, color)
            rect = surf.get_rect(center=(center_x, line_y))
            self.draw_text_with_shadow(line, color, rect.topleft, font=font, surface=self.screen)

    def draw_controls_menu(self, width, height):
        awsd_sprite = self.assets.ui_elements.get("awsd")
        awsd_rect = awsd_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 3.5))
        
        arrows_sprite = self.assets.ui_elements.get("arrows")
        arrows_rect = arrows_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 7.5))

        shift_sprite = self.assets.ui_elements.get("shift")
        shift_rect = shift_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 11))

        tab_sprite = self.assets.ui_elements.get("tab")
        tab_rect = tab_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 14))

        self.draw_text_with_shadow("Controls", "#C0C0C0", ((width // 8) - 100, (height // 16)))
        self.draw_text_with_shadow("Movement", "#C0C0C0", ((width // 8) * 4.5, (height // 8) * 2.5))
        self.draw_text_with_shadow("Selection", "#C0C0C0", ((width // 8) * 4.5, (height // 16) * 10.5))
        self.draw_text_with_shadow("Cycle", "#C0C0C0", ((width // 8) * 4.5, (height // 16) * 13.5))

        self.screen.blit(awsd_sprite, awsd_rect)
        self.screen.blit(arrows_sprite, arrows_rect)
        self.screen.blit(shift_sprite, shift_rect)
        self.screen.blit(tab_sprite, tab_rect)

    def draw_menu(self, menu):
        w, h = self.screen.get_size()
        self.screen.fill((0, 0, 0))
        self.display_animated_screens("title")

        if menu.open_controls_menu:
            self.draw_controls_menu(w, h)
        else:
            title_rect = menu.title_text.get_rect(center=menu.title.center)
            self.draw_text_with_shadow("Faith & Fury", "#C0C0C0", title_rect)
        
        if menu.popup_menu.is_open:
            menu.popup_menu.draw(self.screen)

    def draw_game_world(self, game_state, visibility_map):
        self.screen.fill((32, 32, 32))
        self.draw_map_with_fog(game_state, visibility_map)

        if game_state.selected_unit:
            for tile in (game_state.reachable_tiles or []):
                self.draw_tile_highlight(game_state, tile[0], tile[1], (0, 255, 255, 90))

        if game_state.hovered_tile:
            self.draw_tile_highlight_crimson(game_state, *game_state.hovered_tile)

        render_queue = []
        render_queue.extend(game_state.resources)
        render_queue.extend(game_state.buildings)
        render_queue.extend(game_state.units)

        # Add Enemy Buildings (ONLY if fully visible: visibility_map == 2)
        for eb in game_state.e_buildings:
            ex, ey = int(eb.x), int(eb.y)
            if 0 <= ex < len(visibility_map) and 0 <= ey < len(visibility_map[0]):
                if visibility_map[ex][ey] == 2:
                    render_queue.append(eb)

        # Add Enemy Units (ONLY if fully visible: visibility_map == 2)
        for eu in game_state.enemy_units:
            eux, euy = int(eu.x), int(eu.y)
            if 0 <= eux < len(visibility_map) and 0 <= euy < len(visibility_map[0]):
                if visibility_map[eux][euy] == 2:
                    render_queue.append(eu)

        render_queue.sort(key=lambda obj: (obj.x + obj.y))

        cam_x = game_state.camera_x
        cam_y = game_state.camera_y

        for obj in render_queue:
            if isinstance(obj, ResourceSource):
                obj.draw(
                    self.screen, OFFSET_X, OFFSET_Y, cam_x, cam_y,
                    BASE_TILE_WIDTH, BASE_TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
                    self.assets.resource_sprites, VISIBILITY_MAP=visibility_map
                )
            elif hasattr(obj, 'direction'):  # It's a unit
                loyalty = getattr(obj, 'loyalty', 'player')
                if loyalty == 'player':
                    obj.draw(self.screen, cam_x, cam_y, self.assets.punit_sprites)
                else:
                    obj.draw(self.screen, cam_x, cam_y, self.assets.eunit_sprites)
            elif hasattr(obj, 'hitpoints'):  # It's a building
                loyalty = getattr(obj, 'loyalty', 'player')
                if loyalty == 'player':
                    obj.draw(self.screen, cam_x, cam_y, self.assets.pbuilding_sprites)
                else:
                    obj.draw(self.screen, cam_x, cam_y, self.assets.ebuilding_sprites)

        self.display_resource_bar(game_state)
        self.display_banner(game_state)
        self.display_day_counter(game_state)

        for res_type in RESOURCE_ICONS.keys():
            self.display_resource_icons(game_state, res_type)
        for anim in self.assets.resource_animations.values():
            anim.update()

        game_state.message_box.draw()
        game_state.popup_menu.draw(self.screen)
        game_state.building_menu.draw(self.screen)
        
        self.draw_tactical_map(game_state, visibility_map)
        game_state.fade_manager.draw(self.screen)

    def draw_coords(self, x, y):
        draw_tx = x + OFFSET_X
        draw_ty = y + OFFSET_Y
        return (draw_tx, draw_ty)
    
    def screen_coords(self, x, y, camera_x, camera_y):
        draw_x = x
        draw_y = y

        screen_x = ((draw_x - draw_y) * BASE_TILE_WIDTH // 2 + (SCREEN_WIDTH // 2) + camera_x)
        screen_y = ((draw_x + draw_y) * BASE_TILE_HEIGHT // 2 + (SCREEN_HEIGHT // 4) + camera_y)

        return(screen_x, screen_y)

    def draw_map_with_fog(self, game_state, VISIBILITY_MAP):
        map_data = PLAYABLE_MAP
        for tx in range(len(map_data)):
            for ty in range(len(map_data[tx])):
                if VISIBILITY_MAP[tx][ty] == 0:
                    continue

                draw_tx, draw_ty = self.draw_coords(tx, ty)
                screen_x, screen_y = self.screen_coords(draw_tx, draw_ty, game_state.camera_x, game_state.camera_y)

                tile = map_data[tx][ty]
                sprite = self.assets.terrain_sprites.get(tile)

                if sprite:
                    if VISIBILITY_MAP[tx][ty] == 1:
                        sprite = sprite.copy()
                        sprite.fill(
                            (120, 120, 120, 255),
                            special_flags=pygame.BLEND_RGBA_MULT
                        )

                    self.screen.blit(
                        sprite,
                        (screen_x - BASE_TILE_WIDTH // 2, screen_y)
                    )

                else:
                    pygame.draw.polygon(
                        self.screen,
                        (255, 0, 255),
                        [
                            (screen_x, screen_y),
                            (screen_x + BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),
                            (screen_x, screen_y + BASE_TILE_HEIGHT),
                            (screen_x - BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),
                        ],
                    )

    def draw_tile_highlight(self, game_state, x, y, color):
        draw_tx, draw_ty = self.draw_coords(x, y)
        screen_x, screen_y = self.screen_coords(draw_tx, draw_ty, game_state.camera_x, game_state.camera_y)

        overlay = pygame.Surface((BASE_TILE_WIDTH, BASE_TILE_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(overlay, color, [
            (BASE_TILE_WIDTH // 2, 0),
            (BASE_TILE_WIDTH, BASE_TILE_HEIGHT // 2),
            (BASE_TILE_WIDTH // 2, BASE_TILE_HEIGHT),
            (0, BASE_TILE_HEIGHT // 2)
        ])
        self.screen.blit(overlay, (screen_x - BASE_TILE_WIDTH // 2, screen_y))

    def draw_tile_highlight_crimson(self, game_state, x, y):
        draw_tx, draw_ty = self.draw_coords(x, y)
        screen_x, screen_y = self.screen_coords(draw_tx, draw_ty, game_state.camera_x, game_state.camera_y)

        points = [
            (screen_x, screen_y),
            (screen_x + BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),
            (screen_x, screen_y + BASE_TILE_HEIGHT),
            (screen_x - BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),
        ]

        pygame.draw.polygon(self.screen, (220, 20, 60), points, width=5)
        
    def display_resource_icons(self, game_state, res_type):
        anim = self.assets.resource_animations.get(res_type)
        if not anim: return
        
        w, h = self.screen.get_size()
        sprite = anim.get_current_frame()

        icon_positions = {
            "food": w * 0.11,
            "wood": w * 0.34,
            "gold": w * 0.64,
            "population": w * 0.87
        }

        res_x = icon_positions.get(res_type, 0)
        res_y = 2
        
        rect = sprite.get_rect(topright=(res_x, res_y))
        self.screen.blit(sprite, rect)

    def display_resource_bar(self, game_state):
        bar_sprite = self.assets.ui_elements.get("resource_bar")
        w, h = self.screen.get_size()

        if bar_sprite:
            edge_width = 50 
            
            self.screen.blit(bar_sprite, (0, 0), (0, 0, edge_width, bar_sprite.get_height()))
            
            middle_section = bar_sprite.subsurface((edge_width, 0, bar_sprite.get_width() - (edge_width * 2), bar_sprite.get_height()))
            stretched_middle = pygame.transform.scale(middle_section, (w - (edge_width * 2), bar_sprite.get_height()))
            self.screen.blit(stretched_middle, (edge_width, 0))
            
            self.screen.blit(bar_sprite, (w - edge_width, 0), (bar_sprite.get_width() - edge_width, 0, edge_width, bar_sprite.get_height()))

        text_color = (255, 255, 255)
        font = pygame.font.SysFont(None, 60)

        game_state.population = len(game_state.units)
        max_pop = 0
        for building in game_state.buildings:
            if building.is_constructed:
                max_pop += building.population_limit

        food_text = f" {game_state.food_amount}"
        wood_text = f" {game_state.wood_amount}"
        gold_text = f" {game_state.gold_amount}"
        pop_text = f" {game_state.population} / {max_pop}"

        f_surface = font.render(food_text, True, text_color)
        w_surface = font.render(wood_text, True, text_color)
        g_surface = font.render(gold_text, True, text_color)
        p_surface = font.render(pop_text, True, text_color)

        f_x = w * 0.12
        w_x = w * 0.35
        g_x = w * 0.65
        p_x = w * 0.88

        f_y = (58 - f_surface.get_height())
        w_y = (58 - w_surface.get_height())
        g_y = (58 - g_surface.get_height())
        p_y = (58 - p_surface.get_height())

        self.screen.blit(f_surface, (f_x, f_y))
        self.screen.blit(w_surface, (w_x, w_y))
        self.screen.blit(g_surface, (g_x, g_y))
        self.screen.blit(p_surface, (p_x, p_y))

    def display_banner(self, game_state):
        banner_dict = self.assets.ui_elements.get("banner")
        if not banner_dict:
            return

        faction_key = getattr(game_state, "player_faction", "seljuks").lower() 
        banner_sprite = banner_dict.get(faction_key)
        
        if not banner_sprite:
            return

        w, h = self.screen.get_size()
        banner_x = (w // 2) - (banner_sprite.get_width() // 2)
        banner_y = 0 

        self.screen.blit(banner_sprite, (banner_x, banner_y))

    def display_day_counter(self, game_state):
        self.assets.day_counter_anim.update()
        
        sprite = self.assets.day_counter_anim.get_current_frame()
        if not sprite: 
            return

        text_color = (255, 255, 255)
        font = pygame.font.SysFont(None, 60)
        day_text = f"Day {game_state.day}"
        surface = font.render(day_text, True, text_color)

        sprite_x = 5
        sprite_y = 65

        padding = 10
        text_x = sprite_x + sprite.get_width() + padding
        text_y = sprite_y + (sprite.get_height() // 2) - (surface.get_height() // 2)

        self.screen.blit(sprite, (sprite_x, sprite_y))
        self.screen.blit(surface, (text_x, text_y))
        
    def draw_tactical_map(self, game_state, visibility_map):
        mini_map_surface = pygame.Surface((game_state.minimap_size, game_state.minimap_size), pygame.SRCALPHA)
        
        pygame.draw.circle(mini_map_surface, (32, 32, 32, 200), (game_state.radius, game_state.radius), game_state.smaller_radius)
        
        center_x_grid = (PLAYABLE_WIDTH - 1) / 2.0
        center_y_grid = (PLAYABLE_HEIGHT - 1) / 2.0
        
        offset_x = game_state.radius - int((center_x_grid - center_y_grid) * game_state.mini_map_scale)
        offset_y = game_state.radius - int((center_x_grid + center_y_grid) * game_state.mini_map_scale)
        
        for x in range(PLAYABLE_WIDTH):
            for y in range(PLAYABLE_HEIGHT):
                vis = visibility_map[x][y]
                if vis == 0:
                    continue
                tile = PLAYABLE_MAP[x][y]
                color = TILE_DRAW_COLORS.get(tile, (255, 0, 255))

                draw_x = int((x - y) * game_state.mini_map_scale + offset_x)
                draw_y = int((x + y) * game_state.mini_map_scale + offset_y)
                
                dist_from_center = ((draw_x - game_state.radius) ** 2 + (draw_y - game_state.radius) ** 2) ** 0.5
                if dist_from_center < game_state.smaller_radius:
                    pygame.draw.polygon(mini_map_surface, color, [
                        (draw_x, draw_y - game_state.mini_map_scale),
                        (draw_x + game_state.mini_map_scale, draw_y),
                        (draw_x, draw_y + game_state.mini_map_scale),
                        (draw_x - game_state.mini_map_scale, draw_y)
                    ])

        for unit in game_state.units:
            ux, uy = int(unit.x), int(unit.y)
            if 0 <= ux < PLAYABLE_WIDTH and 0 <= uy < PLAYABLE_HEIGHT and visibility_map[ux][uy] != 0:
                draw_x = int((ux - uy) * game_state.mini_map_scale + offset_x)
                draw_y = int((ux + uy) * game_state.mini_map_scale + offset_y)
                dist_from_center = ((draw_x - game_state.radius) ** 2 + (draw_y - game_state.radius) ** 2) ** 0.5
                if dist_from_center < game_state.smaller_radius:
                    self.draw_unit(ux, uy, mini_map_surface, draw_x, draw_y, game_state)
        
        for building in game_state.buildings:
            bx, by = int(building.x), int(building.y)
            if 0 <= bx < PLAYABLE_WIDTH and 0 <= by < PLAYABLE_HEIGHT and visibility_map[bx][by] != 0:
                draw_x = int((bx - by) * game_state.mini_map_scale + offset_x)
                draw_y = int((bx + by) * game_state.mini_map_scale + offset_y)
                dist_from_center = ((draw_x - game_state.radius) ** 2 + (draw_y - game_state.radius) ** 2) ** 0.5
                if dist_from_center < game_state.smaller_radius:
                    self.draw_building(bx, by, mini_map_surface, draw_x, draw_y, game_state)
        
        for res in game_state.resources:
            rx, ry = int(res.x), int(res.y)
            if 0 <= rx < PLAYABLE_WIDTH and 0 <= ry < PLAYABLE_HEIGHT and visibility_map[rx][ry] != 0:
                draw_x = int((rx - ry) * game_state.mini_map_scale + offset_x)
                draw_y = int((rx + ry) * game_state.mini_map_scale + offset_y)
                dist_from_center = ((draw_x - game_state.radius) ** 2 + (draw_y - game_state.radius) ** 2) ** 0.5
                if dist_from_center < game_state.smaller_radius:
                    self.draw_resource(rx, ry, mini_map_surface, draw_x, draw_y, game_state)
        
        self.map_outline(mini_map_surface, offset_x, offset_y, game_state)
        
        self.screen.blit(mini_map_surface, (game_state.mini_map_center_x - game_state.radius, game_state.mini_map_center_y - game_state.radius))
        pygame.draw.circle(self.screen, (205, 195, 183), (game_state.mini_map_center_x, game_state.mini_map_center_y), game_state.smaller_radius, 5)

    def map_outline(self, surface, offset_x, offset_y, game_state):
        margin = -1 
        corners = [
            (margin, margin),                           # top-left
            (PLAYABLE_WIDTH - 1 - margin, margin),      # top-right
            (PLAYABLE_WIDTH - 1 - margin, PLAYABLE_HEIGHT - 1 - margin),  # bottom-right
            (margin, PLAYABLE_HEIGHT - 1 - margin)      # bottom-left
        ]
        corners_screen = []
        for x, y in corners:
            draw_x = int((x - y) * game_state.mini_map_scale + offset_x)
            draw_y = int((x + y) * game_state.mini_map_scale + offset_y)
            corners_screen.append([draw_x, draw_y])
        if len(corners_screen) >= 3:
            pygame.draw.polygon(surface, (255, 255, 0), corners_screen, 2)

    def draw_unit(self, x, y, surface, draw_x, draw_y, game_state):
        triangle_points = [
            (draw_x, draw_y - HALF_HEIGHT),
            (draw_x - HALF_WIDTH, draw_y + HALF_HEIGHT),
            (draw_x + HALF_WIDTH, draw_y + HALF_HEIGHT),
        ]
        pygame.draw.polygon(surface, (255, 255, 255), triangle_points)

    def draw_building(self, x, y, surface, draw_x, draw_y, game_state):
        size = HALF_WIDTH // 2
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))

    def draw_resource(self, x, y, surface, draw_x, draw_y, game_state):
        circle_radius = HALF_WIDTH // 2
        pygame.draw.circle(surface, (255, 255, 255), (draw_x, draw_y), circle_radius)

    def display_animated_screens(self, name):
        anim = self.assets.animated_sprites.get(name)
        if not anim: return
        
        w, h = self.screen.get_size()
        sprite = anim.get_current_frame()

        if sprite:
            anim.update() 
            rect = sprite.get_rect(topleft=(0, 0))
            self.screen.blit(sprite, rect)

    def day_updates(self, game_state):
        pass