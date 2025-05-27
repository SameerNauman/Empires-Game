import pygame

class MessageBox:
    def __init__(self, screen, visible_width, visible_height):
        self.screen = screen
        self.visible_width = visible_width
        self.visible_height = visible_height
        self.message = ""
        self.font = pygame.font.SysFont("Arial", 20)
        self.visible = False
        self.ok_button_rect = None
        self.padding = 20
        self.box_width = 400

    def open(self, message):
        self.message = message
        self.visible = True  # Reset visibility to ensure it is displayed
        self.ok_button_rect = None  # Reset the OK button rect in case it changes

    def close(self):
        self.visible = False

    def draw(self):
        if not self.visible:
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
        box_height = text_height + 2 * self.padding + 40  # +40 for button space

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

        # Draw OK button (translucent background)
        button_width = 80
        button_height = 30
        button_x = box_x + (self.box_width - button_width) // 2
        button_y = box_y + box_height - button_height - self.padding // 2
        self.ok_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        button_surf = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        button_surf.fill((100, 100, 255, 100))  # Slightly more opaque for the button
        self.screen.blit(button_surf, (button_x, button_y))
        pygame.draw.rect(self.screen, (255, 255, 255), self.ok_button_rect, 2)

        ok_text = self.font.render("OK", True, (255, 255, 255))
        ok_x = button_x + (button_width - ok_text.get_width()) // 2
        ok_y = button_y + (button_height - ok_text.get_height()) // 2
        self.screen.blit(ok_text, (ok_x, ok_y))