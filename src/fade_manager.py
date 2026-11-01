import pygame
from config import *

class FadeManager:
    def __init__(self):
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 0
        self.fade_speed = 8
        self.fade_direction = 1  # 1 for fading out to black, -1 for fading back in
        self.is_fading = False
        
        # Callbacks for actions during peak blackness or completion
        self.mid_fade_callback = None
        self.complete_callback = None
        self.mid_fade_triggered = False

    # Begins the fade out effect
    def start_fade(self):
        self.is_fading = True
        self.fade_direction = 1

    # Advances the fade animation. Returns 'PEAK_BLACK' when the screen is fully dark.
    def update(self):
        if not self.is_fading:
            return

        self.fade_alpha += (self.fade_speed * self.fade_direction)

        # Peak blackness reached (Fade Out complete)
        if self.fade_alpha >= 255 and self.fade_direction == 1:
            self.fade_alpha = 255
            self.fade_direction = -1  # Reverse to fade back in
            return "PEAK_BLACK"

        # Fade In complete
        elif self.fade_alpha <= 0 and self.fade_direction == -1:
            self.fade_alpha = 0
            self.is_fading = False

        return None

    def draw(self, surface):
        if self.is_fading or self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            surface.blit(self.fade_surface, (0, 0))