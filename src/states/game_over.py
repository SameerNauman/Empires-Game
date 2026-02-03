import pygame, sys

class GameOver():
    def __init__(self, screen, game_state_manager, victor):
        self.display = screen
        self.game_state_manager = game_state_manager
        self.victor = victor

        self.font = pygame.font.Font(None, 50)
        self.base_color = "cornflowerblue"
        self.hovering_color = "darkslateblue"

        # --- Define button size and position ---
        self.button_width = 200
        self.button_height = 60

        # Quit button
        self.quit_b = pygame.Rect(0, 0, self.button_width, self.button_height)
        self.quit_b.center = (240, 136)

        # Button text
        self.quit = self.font.render("Quit", True, "black")

        self.selected_button = self.quit_b

    def run(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    if self.selected_button == self.quit_b:
                        pygame.quit()
                        sys.exit()

        # Background
        self.display.fill("cadetblue3")
        # Button rectangles
        pygame.draw.rect(self.display, self.base_color, self.quit_b)

        if self.selected_button == self.quit_b:
            pygame.draw.rect(self.display, self.hovering_color, self.quit_b, 5, 5)


        # Center the text on the button
        quit_rect = self.quit.get_rect(center=self.quit_b.center)

        # Drawing text and buttons
        self.display.blit(self.quit, quit_rect)
