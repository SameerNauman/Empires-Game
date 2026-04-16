import pygame

class MessageBox:
    def __init__(self, screen, visible_width, visible_height):
        self.screen = screen
        self.visible_width = visible_width
        self.visible_height = visible_height
        self.message = ""
        self.font = pygame.font.SysFont("Arial", 20)
        self.visible = False
        self.padding = 20
        self.box_width = 400
        # Timer variables
        self.start_time = 0
        self.duration = 2000 # Duration in milliseconds (2 seconds)

    def open(self, message):
        self.message = message
        self.visible = True  # Reset visibility to ensure it is displayed
        self.start_time = pygame.time.get_ticks()  # Start the timer

    def close(self):
        self.visible = False

    def draw(self):
        if not self.visible:
            return

        # Timer logic
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time >= self.duration:
            self.close()
            return

        # Word wrapping
        words = self.message.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.font.size(test_line)[0] <= self.box_width - 2 * self.padding:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Calculate height
        line_height = self.font.get_height()
        text_height = line_height * len(lines)
        box_height = text_height + 2 * self.padding 

        # Center position based on visible screen
        box_x = (self.visible_width - self.box_width) // 2
        box_y = (self.visible_height - box_height) // 2

        # --- Make translucent background for the message box ---
        translucent_surf = pygame.Surface((self.box_width, box_height), pygame.SRCALPHA)
        translucent_surf.fill((30, 30, 30, 180))  # (R,G,B,Alpha) - alpha 0-255, 180 is partial transparency
        self.screen.blit(translucent_surf, (box_x, box_y))

        # Draw border (solid, not translucent)
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, self.box_width, box_height), 2)

        # Draw text
        for i, line in enumerate(lines):
            text_surf = self.font.render(line, True, (255, 255, 255))
            text_x = box_x + (self.box_width - text_surf.get_width()) // 2
            text_y = box_y + self.padding + i * line_height
            self.screen.blit(text_surf, (text_x, text_y))