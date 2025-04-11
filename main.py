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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zmienne globalne dla metadanych
global_title = None
global_artist = None
global_album = None
global_cover_path = None
global_is_playing = False

should_switch_to_player = False  # Flaga do przełączania na ekran player
should_switch_to_clock = False   # Flaga do przełączania na ekran zegara

def load_metadata():
    """Funkcja, która pobiera metadane z Shairport i aktualizuje zmienne globalne."""
    global global_title, global_artist, global_album, global_cover_path, global_is_playing
    
    try:
        title, artist, album, cover_path = get_current_track_info_shairport()
        
        # Aktualizujemy zmienne globalne tylko jeśli otrzymaliśmy dane
        if title or artist or album:
            global_title = title
            global_artist = artist
            global_album = album
            global_cover_path = cover_path
            global_is_playing = True
            logger.debug(f"Zaktualizowano metadane: {title} - {artist}")
        else:
            # Jeśli nie ma danych, zerujemy status odtwarzania
            global_is_playing = False
            
    except Exception as e:
        logger.error(f"Błąd w load_metadata: {e}")
    
    # Zwracamy aktualne wartości (dla kompatybilności)
    return global_title, global_artist, global_album, global_cover_path

def metadata_thread():
    """Wątek ciągle odświeżający metadane."""
    logger.debug("Uruchomiono wątek metadanych")
    while True:
        try:
            load_metadata()
            time.sleep(5)  # Odczyt co 5 sekund
        except Exception as e:
            logger.error(f"Błąd w wątku metadanych: {e}")
            time.sleep(5)

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
    
    # Uruchamiamy wątek metadanych
    md_thread = threading.Thread(target=metadata_thread, daemon=True)
    md_thread.start()

    current_screen = "clock"
    last_playing_status = None  # Zmienna do monitorowania stanu odtwarzania

    while True:
        # Sprawdzamy stan odtwarzania i aktualizujemy zmienne globalne
        title, artist, album, cover_path = global_title, global_artist, global_album, global_cover_path

        # Automatyczne przełączanie ekranów na podstawie stanu odtwarzania
        if global_is_playing and current_screen == "clock":
            should_switch_to_player = True
        elif not global_is_playing and current_screen == "player":
            should_switch_to_clock = True

        if should_switch_to_player:
            print("[DEBUG] Changing to player screen...")
            current_screen = "player"
            should_switch_to_player = False  # Resetujemy flagę po przełączeniu

        if should_switch_to_clock:
            print("[DEBUG] Changing to clock screen...")
            current_screen = "clock"
            should_switch_to_clock = False  # Resetujemy flagę po przełączeniu

        if current_screen == "clock":
            result = run_clock_screen(screen, test_mode=test_mode)
            if result == "player":
                should_switch_to_player = True  # Ustawiamy flagę do przełączenia na player
            else:
                break
        elif current_screen == "player":
            # Przekazujemy metadane jako parametr do run_player_screen
            result = run_player_screen(
                screen, 
                test_mode=test_mode, 
                metadata={
                    'title': global_title,
                    'artist': global_artist,
                    'album': global_album,
                    'cover_path': global_cover_path,
                    'is_playing': global_is_playing
                }
            )
            if result == "clock":
                should_switch_to_clock = True  # Ustawiamy flagę do przełączenia na clock
            elif not global_is_playing:  # Sprawdzenie, czy muzyka jest zatrzymana
                should_switch_to_clock = True  # Po zakończeniu połączenia przechodzimy na zegar
            else:
                # Muzyka wciąż odtwarzana
                last_playing_status = (title, artist, album, cover_path)
                continue

    # Wyczyść ekran przed wyjściem
    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.delay(200)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()