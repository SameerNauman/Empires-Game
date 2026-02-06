import pygame

class PopupMenu:
    def __init__(self, options,actions, x, y, width=150, item_height=30):
        self.options = options
        self.actions = actions #dictionary to map options to actions
        self.x = x
        self.y = y
        self.width = width
        self.item_height = item_height
        self.selected_index = 0
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 20)

    def open(self, options, actions):
        self.options = options
        self.actions = actions
        self.selected_index = 0
        self.is_open = True

    def close(self):
        self.is_open = False
        self.menu_type = None

    def draw(self, screen):
        if not self.is_open:
            return
        height = self.item_height * len(self.options)
        pygame.draw.rect(screen, (0, 0, 0), (self.x, self.y, self.width, height))
        pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.width, height), 2)

        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_index else (255, 255, 255)
            text = self.font.render(option, True, color)
            screen.blit(text, (self.x + 10, self.y + i * self.item_height + 5))

    def set_position(self, x, y):
        self.x = x
        self.y = y  
        
    def move_selection(self, direction):
        if self.is_open:
            self.selected_index = (self.selected_index + direction) % len(self.options)

    def select(self):
        if self.is_open:
            selected_option = self.options[self.selected_index]
            selected_action = self.actions.get(selected_option)
            if selected_action:
                selected_action()  # Call the selected action
            else:
                print(f"WARNING: No action defined for '{selected_option}'")
            return selected_option
        return None