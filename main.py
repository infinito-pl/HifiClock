import os
import sys
import pygame
import threading
import time
import logging
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import get_current_track_info_shairport

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

should_switch_to_player = False  # Flaga do przełączania na ekran player
should_switch_to_clock = False   # Flaga do przełączania na ekran zegara

def main():
    global should_switch_to_player, should_switch_to_clock

    pygame.init()
    pygame.mixer.quit()

    test_mode = "--test" in sys.argv
    if test_mode:
        screen = pygame.display.set_mode((800, 800))
    else:
        screen = pygame.display.set_mode((800, 800), pygame.FULLSCREEN)

    logger.debug(f"Używany sterownik SDL: {pygame.display.get_driver()}")

    current_screen = "clock"
    last_check_time = time.time()
    CHECK_INTERVAL = 3  # Sprawdzaj co 3 sekundy

    while True:
        current_time = time.time()
        
        # Sprawdź stan odtwarzania co określony interwał
        if current_time - last_check_time >= CHECK_INTERVAL:
            last_check_time = current_time
            title, artist, album, cover_path = get_current_track_info_shairport()
            
            # Jeśli mamy dane o utworze i jesteśmy na ekranie zegara
            if title and artist and current_screen == "clock":
                logger.debug("Wykryto aktywny strumień, przełączam na ekran odtwarzacza")
                should_switch_to_player = True
                should_switch_to_clock = False
            
            # Jeśli nie ma danych o utworze i jesteśmy na ekranie odtwarzacza
            elif not title and not artist and current_screen == "player":
                logger.debug("Brak aktywnych danych, przełączam na ekran zegara")
                should_switch_to_player = False
                should_switch_to_clock = True

        # Obsługa przełączania ekranów
        if should_switch_to_player and current_screen == "clock":
            logger.debug("Przełączanie na ekran odtwarzacza")
            current_screen = "player"
            should_switch_to_player = False

        if should_switch_to_clock and current_screen == "player":
            logger.debug("Przełączanie na ekran zegara")
            current_screen = "clock"
            should_switch_to_clock = False

        # Uruchom odpowiedni ekran
        try:
            if current_screen == "clock":
                result = run_clock_screen(screen, test_mode=test_mode)
                if result == "player":
                    should_switch_to_player = True
                elif result == "quit":
                    break
            else:
                result = run_player_screen(screen, test_mode=test_mode)
                if result == "clock":
                    should_switch_to_clock = True
                elif result == "quit":
                    break
        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania ekranu {current_screen}: {e}")
            break

    # Wyczyść ekran przed wyjściem
    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.delay(200)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()