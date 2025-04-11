import os
import sys
import pygame
import threading
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from utils.logging import logger
from ui.screens.clock import ClockScreen
from ui.screens.player import PlayerScreen
from services.metadata.shairport import get_current_track_info

def main():
    try:
        # Inicjalizacja Pygame
        pygame.init()
        pygame.mixer.quit()
        
        # Ustawienie trybu wyświetlania
        test_mode = "--test" in sys.argv
        if test_mode:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        
        logger.info(f"Current SDL driver: {pygame.display.get_driver()}")
        
        # Inicjalizacja ekranów
        clock_screen = ClockScreen(screen, test_mode)
        player_screen = PlayerScreen(screen, test_mode)
        
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