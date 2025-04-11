import os
import sys
import pygame
import threading
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from utils.logging import logger
from ui.screens.clock import ClockScreen
from ui.screens.player import PlayerScreen
from services.metadata.shairport import get_current_track_info

def main():
    try:
        # Inicjalizacja Pygame
        pygame.init()
        pygame.mixer.quit()
        pygame.mouse.set_visible(False)
        
        # Utwórz ekran
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("HifiClock")
        
        logger.info(f"Current SDL driver: {pygame.display.get_driver()}")
        
        # Inicjalizacja ekranów
        clock_screen = ClockScreen(screen)
        player_screen = PlayerScreen(screen)
        
        current_screen = "clock"
        last_metadata = None
        
        while True:
            # Pobierz aktualne metadane
            metadata = get_current_track_info()
            
            # Sprawdź czy metadane się zmieniły
            if metadata != last_metadata:
                last_metadata = metadata
                title, artist, album, _ = metadata
                
                # Jeśli nie ma metadanych, przejdź do ekranu zegara
                if not any([title, artist, album]):
                    current_screen = "clock"
            
            # Uruchom odpowiedni ekran
            if current_screen == "clock":
                result = clock_screen.run()
                if result == "player":
                    current_screen = "player"
                elif result == "quit":
                    break
            elif current_screen == "player":
                result = player_screen.run()
                if result == "clock":
                    current_screen = "clock"
                elif result == "quit":
                    break
    
    except Exception as e:
        logger.error(f"Błąd w głównej pętli aplikacji: {e}")
    finally:
        # Wyczyść ekran przed wyjściem
        screen.fill((0, 0, 0))
        pygame.display.flip()
        pygame.time.delay(200)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()