import pygame

class AnimatedSprite:
    def __init__(self, full_path, rows, cols, animation_speed=0.15):
        self.frames = self._load_frames(full_path, rows, cols)
        self.total_frames = len(self.frames)
        self.animation_speed = animation_speed
        self.current_frame = 0

    def _load_frames(self, path, rows, cols):
        """Slices the sheet and returns a list of surfaces."""
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading {path}: {e}")
            return []

        sheet_rect = sheet.get_rect()
        frame_width = sheet_rect.width // cols
        frame_height = sheet_rect.height // rows
        
        frames = []
        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(c * frame_width, r * frame_height, frame_width, frame_height)
                frame = pygame.Surface(rect.size, pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), rect)
                frames.append(frame)
        return frames

    def update(self):
        self.current_frame += self.animation_speed
        if self.current_frame >= self.total_frames:
            self.current_frame = 0

    def get_current_frame(self):
        if not self.frames: return None
        return self.frames[int(self.current_frame)]