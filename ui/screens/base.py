import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from utils.logging import logger

class BaseScreen:
    def __init__(self, screen, test_mode=False):
        self.screen = screen
        self.test_mode = test_mode
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.background_color = COLORS['BACKGROUND']
        self.clock = pygame.time.Clock()
        self.running = True
        self.start_y = None
        self.SWIPE_THRESHOLD = 0.25

    def handle_events(self):
        """Obsługuje zdarzenia."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"
            elif event.type == pygame.FINGERDOWN:
                self.start_y = event.y * self.height
            elif event.type == pygame.FINGERUP and self.start_y is not None:
                end_y = event.y * self.height
                delta_y = self.start_y - end_y
                if delta_y > self.SWIPE_THRESHOLD:
                    pygame.event.clear()
                    return "swipe_up"
                elif delta_y < -self.SWIPE_THRESHOLD:
                    pygame.event.clear()
                    return "swipe_down"
                self.start_y = None
        return None

    def update(self):
        """Aktualizuje stan ekranu."""
        pass

    def draw(self):
        """Rysuje ekran."""
        self.screen.fill(self.background_color)

    def run(self):
        """Główna pętla ekranu."""
        while self.running:
            result = self.handle_events()
            if result:
                return result

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        return "quit" 