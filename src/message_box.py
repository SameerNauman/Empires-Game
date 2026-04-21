import pygame
from config import *

class MessageBox:
    def __init__(self, screen, visible_width, visible_height, sprite):
        self.screen = screen
        self.sprite = sprite
        self.visible_width = visible_width
        self.visible_height = visible_height
        self.message = ""
        self.font = pygame.font.SysFont("Arial", 20)
        self.visible = False
        self.padding = 20
        self.padding_right = 80
        self.box_width = 1000
        self.box_height = 150
        # Timer variables
        self.start_time = 0
        self.duration = 2000 # Duration in milliseconds (2 seconds)

    def open(self, message, error_message):
        self.message = message
        self.error_message = error_message
        self.visible = True  # Reset visibility to ensure it is displayed
        self.start_time = pygame.time.get_ticks()  # Start the timer

    def close(self):
        self.visible = False

    def countdown(self):
        
        # Timer logic
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time >= self.duration:
            self.close()
            return

    def draw(self):
        if not self.visible:
            return
        
        if self.error_message:
            self.countdown()

        lines = []
        paragraphs = self.message.split('\n')

        for paragraph in paragraphs:
            # If it's an intentional empty line (double \n), add a spacer
            if not paragraph.strip() and len(paragraph) == 0:
                lines.append("")
                continue
                
            words = paragraph.split(' ')
            current_line = ""
            
            for word in words:
                if not word: continue # Skip accidental double spaces
                
                test_line = f"{current_line} {word}".strip()
                if self.font.size(test_line)[0] <= self.box_width - self.padding - self.padding_right:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            
            # Only append if there's actually text left over
            if current_line:
                lines.append(current_line)

        # Center position logic
        box_x = 0
        # We use self.box_height (300) now instead of a variable text_height
        box_y = SCREEN_HEIGHT - self.box_height

        # --- DRAW THE SPRITE ---
        # This replaces the translucent_surf and the white border lines
        self.screen.blit(self.sprite, (box_x, box_y))

        # Draw text (Start from the same box_x/box_y)
        line_height = self.font.get_height()
        for i, line in enumerate(lines):
            text_surf = self.font.render(line, True, (255, 255, 255))
            text_x = box_x + self.padding
            text_y = box_y + self.padding + i * line_height
            self.screen.blit(text_surf, (text_x, text_y))