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

    # Startup state faction selection carousel.
    def draw_startup(self, startup):
        w, h = self.screen.get_size()
        self.screen.fill((0, 0, 0))

        # Display title animation using AssetManager
        anim = self.assets.animated_sprites.get("title")
        if anim:
            sprite = anim.get_current_frame()
            if sprite:
                anim.update()
                self.screen.blit(sprite, (0, 0))

        # Determine title (Only 2 steps now: 0 = Player Faction, 1 = Enemy Faction)
        if startup.step == 0:
            title = "Select Player Faction"
        else:
            title = "Select Enemy Faction"
            
        current_list = startup.factions

        # Draw Header
        title_rect = self.font.render(title, True, "#C0C0C0").get_rect(center=(w // 2, h // 4))
        self.draw_text_with_shadow(title, "#C0C0C0", title_rect.topleft)

        # Smooth Lerp for Continuous Scroll Position
        startup.scroll_pos += (startup.target_scroll_pos - startup.scroll_pos) * 0.15

        # === CAROUSEL VIEWPORT FRAME ===
        card_bg = self.assets.ui_elements.get("carousel")
        if card_bg:
            card_w, card_h = card_bg.get_size()
        else:
            card_w, card_h = 240, 140

        viewport_width = 750
        viewport_height = card_h + 10
        viewport_rect = pygame.Rect(0, 0, viewport_width, viewport_height)
        viewport_rect.center = (w // 2, h // 2)

        pygame.draw.rect(self.screen, (60, 50, 40), viewport_rect.inflate(6, 6), border_radius=4)
        pygame.draw.rect(self.screen, (20, 20, 20), viewport_rect, border_radius=2)

        # Set clipping region
        self.screen.set_clip(viewport_rect)

        num_items = len(current_list)
        center_x = viewport_rect.centerx
        center_y = viewport_rect.centery
        base_idx = int(math.floor(startup.scroll_pos))

        for i in range(-2, 3):
            item_index = (base_idx + i) % num_items
            item_text = current_list[item_index]

            slot_x = center_x + ((base_idx + i - startup.scroll_pos) * startup.slot_width)

            if viewport_rect.left - 200 < slot_x < viewport_rect.right + 200:
                distance_from_center = abs(slot_x - center_x)
                is_selected = distance_from_center < (startup.slot_width / 2.0)

                # Render native sprite
                if card_bg:
                    card_rect = card_bg.get_rect(center=(int(slot_x), center_y))
                    self.screen.blit(card_bg, card_rect)
                else:
                    card_rect = pygame.Rect(0, 0, card_w, card_h)
                    card_rect.center = (int(slot_x), center_y)
                    pygame.draw.rect(self.screen, (40, 40, 40), card_rect, border_radius=4)
                    pygame.draw.rect(self.screen, (100, 100, 100), card_rect, 2, border_radius=4)

                # Item label text centered cleanly in the card frame
                text_color = "#FFD700" if is_selected else "#A0A0A0"
                txt_surf = self.small_font.render(item_text, True, text_color)
                txt_rect = txt_surf.get_rect(center=(int(slot_x), center_y))
                self.screen.blit(txt_surf, txt_rect)

        # Reset clipping region
        self.screen.set_clip(None)

        # Draw footer instructions
        instructions = "Use A/D or Left/Right to Cycle | LSHIFT to Select | ESC to Back"
        inst_rect = self.small_font.render(instructions, True, "#C0C0C0").get_rect(center=(w // 2, (h // 8) * 7))
        self.draw_text_with_shadow(instructions, "#C0C0C0", inst_rect.topleft, font=self.small_font, surface=self.screen)

    # Controls state drawing
    # Draws the controls menu on the display surface. It displays the control sprites and their corresponding labels.
    def draw_controls_menu(self, width, height):
        # Sprites
        awsd_sprite = self.assets.ui_elements.get("awsd")
        awsd_rect = awsd_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 3.5))
        
        arrows_sprite = self.assets.ui_elements.get("arrows")
        arrows_rect = arrows_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 7.5))

        shift_sprite = self.assets.ui_elements.get("shift")
        shift_rect = shift_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 11))

        tab_sprite = self.assets.ui_elements.get("tab")
        tab_rect = tab_sprite.get_rect(center=((width // 8) * 7, (height // 16) * 14))

        # Text
        self.draw_text_with_shadow("Controls", "#C0C0C0", ((width // 8) - 100, (height // 16)))
        self.draw_text_with_shadow("Movement", "#C0C0C0", ((width // 8) * 4.5, (height // 8) * 2.5))
        self.draw_text_with_shadow("Selection", "#C0C0C0", ((width // 8) * 4.5, (height // 16) * 10.5))
        self.draw_text_with_shadow("Cycle", "#C0C0C0", ((width // 8) * 4.5, (height // 16) * 13.5))

        # Display Sprites
        self.screen.blit(awsd_sprite, awsd_rect)
        self.screen.blit(arrows_sprite, arrows_rect)
        self.screen.blit(shift_sprite, shift_rect)
        self.screen.blit(tab_sprite, tab_rect)

    # Menu state drawing
    # Draws the menu on the display surface. It handles the rendering of the background, title, controls menu, popup menu,
    # and fade transition effect. The method also manages the state transitions between the main menu and the controls menu.
    def draw_menu(self, menu):
        w, h = self.screen.get_size()

        # Clear the screen surface with a black background before drawing the menu elements.
        self.screen.fill((0, 0, 0))

        # Animated Screens
        self.display_animated_screens("title")

        # Controls menu
        if menu.open_controls_menu:
            self.draw_controls_menu(w, h)
        else:
            # Title
            title_rect = menu.title_text.get_rect(center=menu.title.center)
            self.draw_text_with_shadow("Faith & Fury", "#C0C0C0", title_rect)
        
        if menu.popup_menu.is_open:
            menu.popup_menu.draw(self.screen)

    # Draws the entire game world, including terrain, units, buildings, resources, and UI elements. It respects the fog of war and
    # depth-sorts all entities for proper rendering order. The method also handles drawing the HUD, resource bar, banners, day counter,
    # minimap, and any active fade effects.
    def draw_game_world(self, game_state, visibility_map):
        # Clear screen / Background
        self.screen.fill((32, 32, 32))

        # Draw terrain map first (respecting Fog of War: 0=hidden, 1=explored/darkened, 2=visible)
        self.draw_map_with_fog(game_state, visibility_map)

        # Draw tile highlights (reachable tiles & hovered tiles)
        if game_state.selected_unit:
            for tile in (game_state.reachable_tiles or []):
                self.draw_tile_highlight(game_state, tile[0], tile[1], (0, 255, 255, 90))

        if game_state.hovered_tile:
            self.draw_tile_highlight_crimson(game_state, *game_state.hovered_tile)

        # Build a single, unified render queue for all world objects 
        # (Resources, Buildings, Units) so they depth-sort correctly together!
        render_queue = []

        # Add Resources
        render_queue.extend(game_state.resources)

        # Add Player Buildings & Units
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

        # Sort everything strictly by isometric depth (x + y)
        render_queue.sort(key=lambda obj: (obj.x + obj.y))

        cam_x = game_state.camera_x
        cam_y = game_state.camera_y

        # Draw all world entities in a single pass
        for obj in render_queue:
            if isinstance(obj, ResourceSource):
                obj.draw(
                    self.screen, OFFSET_X, OFFSET_Y, cam_x, cam_y,
                    BASE_TILE_WIDTH, BASE_TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
                    self.assets.resource_sprites, VISIBILITY_MAP=visibility_map
                )
            elif hasattr(obj, 'direction'):  # It's a unit
                obj.draw(self.screen, cam_x, cam_y, self.assets.unit_sprites)
            elif hasattr(obj, 'hitpoints'):  # It's a building
                obj.draw(self.screen, cam_x, cam_y, self.assets.building_sprites)

        # Draw HUD & UI on top of the world
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
        
        # Minimap & Screen Fades
        self.draw_tactical_map(game_state, visibility_map)
        game_state.fade_manager.draw(self.screen)

    # Returns (draw_tx, draw_ty)
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

    # Displays the sprites for the terrain, and magenta for missing sprites
    def draw_map_with_fog(self, game_state, VISIBILITY_MAP):
        map_data = PLAYABLE_MAP
        for tx in range(len(map_data)):
            for ty in range(len(map_data[tx])):
                # Skip unseen tiles
                if VISIBILITY_MAP[tx][ty] == 0:
                    continue

                draw_tx, draw_ty = self.draw_coords(tx, ty)
                screen_x, screen_y = self.screen_coords(draw_tx, draw_ty, game_state.camera_x, game_state.camera_y)

                tile = map_data[tx][ty]
                sprite = self.assets.terrain_sprites.get(tile)

                if sprite:
                    # Darken if explored but not currently visible
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
                    # If there isnt a sprite, draw a magenta tile
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

    # Displays highlighted reachable tiles
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

    # Displays the red hovered tile
    def draw_tile_highlight_crimson(self, game_state, x, y):
        draw_tx, draw_ty = self.draw_coords(x, y)
        screen_x, screen_y = self.screen_coords(draw_tx, draw_ty, game_state.camera_x, game_state.camera_y)

        # Define the diamond shape points
        points = [
            (screen_x, screen_y),  # top
            (screen_x + BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),  # right
            (screen_x, screen_y + BASE_TILE_HEIGHT),  # bottom
            (screen_x - BASE_TILE_WIDTH // 2, screen_y + BASE_TILE_HEIGHT // 2),  # left
        ]

        # Draw the outline, not a filled polygon
        pygame.draw.polygon(self.screen, (220, 20, 60), points, width=5)
        
    # Displays the resource icons in the top right corner of the screen, with animation.
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

    # Displays the resource bar at the top of the screen
    def display_resource_bar(self, game_state):
        bar_sprite = self.assets.ui_elements.get("resource_bar")
        w, h = self.screen.get_size() # Get live width

        if bar_sprite:
            # 3 slice
            edge_width = 50 
            
            # Left Cap
            self.screen.blit(bar_sprite, (0, 0), (0, 0, edge_width, bar_sprite.get_height()))
            
            # Middle (Stretched)
            middle_section = bar_sprite.subsurface((edge_width, 0, bar_sprite.get_width() - (edge_width * 2), bar_sprite.get_height()))
            stretched_middle = pygame.transform.scale(middle_section, (w - (edge_width * 2), bar_sprite.get_height()))
            self.screen.blit(stretched_middle, (edge_width, 0))
            
            # Right Cap
            self.screen.blit(bar_sprite, (w - edge_width, 0), (bar_sprite.get_width() - edge_width, 0, edge_width, bar_sprite.get_height()))

        text_color = (255, 255, 255)
        font = pygame.font.SysFont(None, 60)

        # Population
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

        # dynamic text positions.
        f_x = w * 0.12  # Food at ~12%
        w_x = w * 0.35  # Wood at ~35%
        g_x = w * 0.65  # Gold at ~65%
        p_x = w * 0.88  # Pop at ~88%

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

        faction_key = getattr(game_state, "player_faction", "seljuk").lower() 
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
        
    # Displays a circular mini map in the bottom right corner of the screen.
    def draw_tactical_map(self, game_state, visibility_map):
        # Mini map dimensions and position
        
        # Create a surface for the circular mini map with per-pixel alpha
        mini_map_surface = pygame.Surface((game_state.minimap_size, game_state.minimap_size), pygame.SRCALPHA)
        
        # Draw semi-transparent circular background - smaller circle
        # circle_radius = int(RADIUS * 0.85)
        pygame.draw.circle(mini_map_surface, (32, 32, 32, 200), (game_state.radius, game_state.radius), game_state.smaller_radius)
        
        # Calculate offset to center the map on the minimap center
        center_sum = (PLAYABLE_WIDTH + PLAYABLE_HEIGHT - 2) // 2
        offset_x = game_state.radius
        offset_y = game_state.radius - center_sum * game_state.mini_map_scale
        
        # Draw only visible tiles
        for x in range(PLAYABLE_WIDTH):
            for y in range(PLAYABLE_HEIGHT):
                vis = visibility_map[x][y]
                if vis == 0:
                    continue  # Skip tiles not visible
                tile = PLAYABLE_MAP[x][y]
                color = TILE_DRAW_COLORS.get(tile, (255, 0, 255))

                draw_x = int((x - y) * game_state.mini_map_scale + offset_x)
                draw_y = int((x + y) * game_state.mini_map_scale + offset_y)
                
                # Check if point is within circle before drawing
                dist_from_center = ((draw_x - game_state.radius) ** 2 + (draw_y - game_state.radius) ** 2) ** 0.5
                if dist_from_center < game_state.smaller_radius:
                    # Top-down diamond tile
                    pygame.draw.polygon(mini_map_surface, color, [
                        (draw_x, draw_y - game_state.mini_map_scale),
                        (draw_x + game_state.mini_map_scale, draw_y),
                        (draw_x, draw_y + game_state.mini_map_scale),
                        (draw_x - game_state.mini_map_scale, draw_y)
                    ])

        # Only draw player units/buildings/resources if on visible tiles
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
        
        # Blit the mini map surface to the screen
        self.screen.blit(mini_map_surface, (game_state.mini_map_center_x - game_state.radius, game_state.mini_map_center_y - game_state.radius))
        
        # Draw circular border
        pygame.draw.circle(self.screen, (205, 195, 183), (game_state.mini_map_center_x, game_state.mini_map_center_y), game_state.smaller_radius, 5)

    def map_outline(self, surface, offset_x, offset_y, game_state):
        # Draw yellow outline around playable map with margin
        margin = -1  # tile margin inward from edges
        corners = [
            (margin, margin),                           # top-left
            (PLAYABLE_WIDTH - 1 - margin, margin),      # top-right
            (PLAYABLE_WIDTH - 1 - margin, PLAYABLE_HEIGHT - 1 - margin),  # bottom-right
            (margin, PLAYABLE_HEIGHT - 1 - margin)      # bottom-left
        ]
        # Top-down diamond view (rotate 45 degrees without isometric compression)
        corners_screen = []
        for x, y in corners:
            draw_x = int((x - y) * game_state.mini_map_scale + offset_x)
            draw_y = int((x + y) * game_state.mini_map_scale + offset_y)
            corners_screen.append([draw_x, draw_y])
        # Draw diamond outline using polygon (unfilled, just the border)
        if len(corners_screen) >= 3:
            pygame.draw.polygon(surface, (255, 255, 0), corners_screen, 2)

    # Displays units on the map
    def draw_unit(self, x, y, surface, draw_x, draw_y, game_state):
        triangle_points = [
            (draw_x, draw_y - HALF_HEIGHT),
            (draw_x - HALF_WIDTH, draw_y + HALF_HEIGHT),
            (draw_x + HALF_WIDTH, draw_y + HALF_HEIGHT),
        ]
        pygame.draw.polygon(surface, (255, 255, 255), triangle_points)

    # Displays buildings on the map
    def draw_building(self, x, y, surface, draw_x, draw_y, game_state):
        size = HALF_WIDTH // 2
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(draw_x - size, draw_y - size, size * 2, size * 2))

    # Displays resources on the map
    def draw_resource(self, x, y, surface, draw_x, draw_y, game_state):
        circle_radius = HALF_WIDTH // 2
        pygame.draw.circle(surface, (255, 255, 255), (draw_x, draw_y), circle_radius)

    # Displays the current frame of the animated screen specified by 'name' on the display surface.
    def display_animated_screens(self, name):
        anim = self.assets.animated_sprites.get(name)
        if not anim: return
        
        w, h = self.screen.get_size()
        sprite = anim.get_current_frame()

        if sprite:
            # Update the animation frame based on the elapsed time and blit it to the display surface
            anim.update() 
            
            rect = sprite.get_rect(topleft=(0, 0))
            self.screen.blit(sprite, rect)