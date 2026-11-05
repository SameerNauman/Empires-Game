import pygame
from config import *

class FadeManager:
    def __init__(self):
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 0
        self.fade_speed = 12
        self.fade_direction = 1  # 1 = fading out (to black), -1 = fading in (from black)
        self.is_fading = False

    def start_fade(self):
        self.is_fading = True
        self.fade_alpha = 0
        self.fade_direction = 1

    def update(self):
        if not self.is_fading:
            return None

        self.fade_alpha += (self.fade_speed * self.fade_direction)

        # 1. Peak black reached -> Start fading back in, return PEAK_BLACK
        if self.fade_alpha >= 255 and self.fade_direction == 1:
            self.fade_alpha = 255
            self.fade_direction = -1
            return "PEAK_BLACK"

        # 2. Fade in completed -> Stop fading, return FADE_COMPLETE
        elif self.fade_alpha <= 0 and self.fade_direction == -1:
            self.fade_alpha = 0
            self.is_fading = False
            return "FADE_COMPLETE"

        return None

    def draw(self, surface):
        if self.is_fading or self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            surface.blit(self.fade_surface, (0, 0))