import pygame, sys

class Menu():
    def __init__(self, screen, game_state_manager):
        self.display = screen
        self.game_state_manager = game_state_manager

        self.font = pygame.font.Font(None, 50)
        self.base_color = "cornflowerblue"
        self.hovering_color = "darkslateblue"

        # --- Define button size and position ---
        self.button_width = 200
        self.button_height = 60

        # Start button
        self.start_b = pygame.Rect(0, 0, self.button_width, self.button_height)
        self.start_b.center = (240, 60)
        # Quit button
        self.quit_b = pygame.Rect(0, 0, self.button_width, self.button_height)
        self.quit_b.center = (240, 150)

        # Button text
        self.start = self.font.render("Start", True, "black")
        self.quit = self.font.render("Quit", True, "black")

        self.selected_button = self.start_b

    def run(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.selected_button == self.quit_b:
                    self.selected_button = self.start_b
                if event.key == pygame.K_DOWN and self.selected_button == self.start_b:
                    self.selected_button = self.quit_b
                if event.key == pygame.K_LSHIFT:
                    if self.selected_button == self.start_b:
                        self.game_state_manager.set_state("gameplay state")
                    else:
                        pygame.quit()
                        sys.exit()

        # Background
        self.display.fill("cadetblue3")
        # Button rectangles
        pygame.draw.rect(self.display, self.base_color, self.start_b)
        pygame.draw.rect(self.display, self.base_color, self.quit_b)

        if self.selected_button == self.start_b:
            pygame.draw.rect(self.display, self.hovering_color, self.start_b, 5, 5)
        else:            
            pygame.draw.rect(self.display, self.hovering_color, self.quit_b, 5, 5)

        # Center the text on the button
        start_rect = self.start.get_rect(center=self.start_b.center)
        quit_rect = self.quit.get_rect(center=self.quit_b.center)

        # Drawing text and buttons
        self.display.blit(self.start, start_rect)
        self.display.blit(self.quit, quit_rect)
