import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from utils.logging import logger

class BaseScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.start_x = 0
        self.start_y = 0

    def handle_events(self):
        """Obsługuje zdarzenia ekranu."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.FINGERDOWN:
                self.start_x = event.x * self.width
                self.start_y = event.y * self.height
            elif event.type == pygame.FINGERUP:
                end_x = event.x * self.width
                end_y = event.y * self.height
                dx = end_x - self.start_x
                dy = end_y - self.start_y
                
                # Sprawdź gest przesunięcia w górę
                if abs(dy) > 50 and dy < 0 and abs(dx) < 50:
                    return "clock"
                # Sprawdź gest przesunięcia w dół
                elif abs(dy) > 50 and dy > 0 and abs(dx) < 50:
                    return "player"
        return None

    def update(self):
        """Aktualizuje stan ekranu."""
        pass

    def draw(self):
        """Rysuje zawartość ekranu."""
        self.screen.fill(COLORS["BACKGROUND"])

    def run(self):
        """Główna pętla ekranu."""
        running = True
        while running:
            result = self.handle_events()
            if result:
                return result
            
            self.update()
            self.draw()
            pygame.display.flip()
            pygame.time.Clock().tick(60) 