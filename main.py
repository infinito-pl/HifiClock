import os
import sys
import pygame
import threading
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import (
    read_shairport_metadata,
    should_switch_to_player_screen,
    should_switch_to_clock_screen,
    reset_switch_flags
)
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

should_switch_to_player = False  # Flaga do przełączania na ekran player
should_switch_to_clock = False   # Flaga do przełączania na ekran zegara

def load_metadata():
    """Funkcja, która będzie odpowiedzialna za pobieranie metadanych w tle."""
    title, artist, album, cover_path = get_current_track_info_shairport()
    return title, artist, album, cover_path

def get_current_track_info_shairport():
    # Mock function to emulate getting track info from Shairport
    # Replace this with actual implementation
    return None, None, None, None

def start_shairport_listener():
    """Uruchamia listener Shairport w osobnym wątku."""
    thread = threading.Thread(target=read_shairport_metadata, daemon=True)
    thread.start()
    logger.debug("Shairport listener started in background thread")

def main():
    global should_switch_to_player, should_switch_to_clock

    pygame.init()
    pygame.mixer.quit()

    test_mode = "--test" in sys.argv
    if test_mode:
        screen = pygame.display.set_mode((800, 800))
    else:
        screen = pygame.display.set_mode((800, 800), pygame.FULLSCREEN)

    print("Current SDL driver:", pygame.display.get_driver())

    current_screen = "clock"
    last_playing_status = None  # Zmienna do monitorowania stanu odtwarzania

    # Uruchom listener Shairport w tle
    start_shairport_listener()

    try:
        while True:
            # Uruchamiamy pobieranie metadanych w tle
            title, artist, album, cover_path = load_metadata()

            # Sprawdź czy należy przełączyć ekran
            if should_switch_to_player_screen() and current_screen == "clock":
                logger.debug("Switching to player screen")
                current_screen = "player"
                reset_switch_flags()
            elif should_switch_to_clock_screen() and current_screen == "player":
                logger.debug("Switching to clock screen")
                current_screen = "clock"
                reset_switch_flags()

            if current_screen == "clock":
                result = run_clock_screen(screen, test_mode=test_mode)
                if result == "player":
                    should_switch_to_player = True  # Ustawiamy flagę do przełączenia na player
                else:
                    break
            elif current_screen == "player":
                result = run_player_screen(screen, test_mode=test_mode)
                if result == "clock":
                    should_switch_to_clock = True  # Ustawiamy flagę do przełączenia na clock
                elif title is None or artist is None:  # Sprawdzenie, czy muzyka jest zatrzymana
                    should_switch_to_clock = True  # Po zakończeniu połączenia przechodzimy na zegar
                else:
                    # Muzyka wciąż odtwarzana
                    last_playing_status = (title, artist, album, cover_path)
                    continue

    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        # Wyczyść ekran przed wyjściem
        screen.fill((0, 0, 0))
        pygame.display.flip()
        pygame.time.delay(200)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()