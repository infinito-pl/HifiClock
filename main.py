#!/usr/bin/env python3
import os
import sys
import time
import importlib
import signal
import threading
import pygame
import logging
from services.shairport_listener import get_current_track_info_shairport

# Konfiguracja logowania 
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Ścieżka bazowa projektu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Globalne zmienne dla metadanych
global_title = None
global_artist = None
global_album = None
global_cover_path = None
global_is_playing = False
last_screen_switch_time = 0
COOLDOWN_PERIOD = 5  # 5 sekund cooldownu między zmianami ekranów

def load_metadata():
    """Ładuje metadane z Shairport i aktualizuje globalne zmienne."""
    global global_title, global_artist, global_album, global_cover_path, global_is_playing
    try:
        logger.debug("Pobieranie informacji o utworze z Shairport")
        track_info = get_current_track_info_shairport()
        if track_info:
            title, artist, album, cover_path = track_info
            if title and artist:  # Mamy prawidłowe dane
                global_title = title
                global_artist = artist
                global_album = album
                global_cover_path = cover_path
                global_is_playing = True
                logger.debug(f"Zaktualizowane metadane: {title} - {artist} - {album}")
                return True
        # Jeśli nie ma danych lub brak tytułu/artysty
        return False
    except Exception as e:
        logger.error(f"Błąd podczas pobierania metadanych: {e}")
        return False

def metadata_thread():
    """Funkcja wątku odświeżająca metadane co 5 sekund."""
    while True:
        try:
            load_metadata()
            time.sleep(5)  # Odśwież co 5 sekund
        except Exception as e:
            logger.error(f"Błąd w wątku metadanych: {e}")
            time.sleep(5)  # Kontynuuj mimo błędu

def main(test_mode=False):
    """
    Główna funkcja aplikacji.
    
    Args:
        test_mode (bool): Czy aplikacja jest uruchomiona w trybie testowym.
    """
    global last_screen_switch_time
    
    logger.info("Uruchamianie aplikacji HifiClock")
    
    # Inicjalizacja Pygame
    pygame.init()
    
    # Konfiguracja wyświetlania
    if test_mode:
        screen = pygame.display.set_mode((800, 480))
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    
    pygame.display.set_caption("HifiClock")
    
    # Uruchom wątek odświeżający metadane
    metadata_refresh_thread = threading.Thread(target=metadata_thread, daemon=True)
    metadata_refresh_thread.start()
    
    # Importuj ekrany dynamicznie
    try:
        logger.debug("Importowanie modułów ekranów")
        run_clock_screen = importlib.import_module("assets.screens.clock").run_clock_screen
        run_player_screen = importlib.import_module("assets.screens.player").run_player_screen
    except ImportError as e:
        logger.error(f"Błąd importowania modułów: {e}")
        pygame.quit()
        sys.exit(1)
    
    # Rozpocznij od ekranu zegara
    current_screen = "clock"
    
    try:
        # Główna pętla aplikacji
        while True:
            current_time = time.time()
            
            # Sprawdź stan odtwarzania i automatycznie przełącz ekran jeśli potrzeba
            if global_is_playing and current_screen == "clock" and (current_time - last_screen_switch_time) > COOLDOWN_PERIOD:
                logger.debug("Wykryto odtwarzanie, przełączam na ekran odtwarzacza")
                current_screen = "player"
                last_screen_switch_time = current_time
            
            # Uruchom odpowiedni ekran
            if current_screen == "clock":
                logger.debug("Uruchamianie ekranu zegara")
                result = run_clock_screen(screen)
                if result == "player":
                    logger.debug("Przełączanie z zegara na odtwarzacz")
                    current_screen = "player"
                    last_screen_switch_time = current_time
                elif result is None:
                    break  # Zakończ aplikację
            
            elif current_screen == "player":
                logger.debug("Uruchamianie ekranu odtwarzacza")
                # Przekaż metadane jako słownik
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
                    logger.debug("Przełączanie z odtwarzacza na zegar")
                    current_screen = "clock"
                    last_screen_switch_time = current_time
                elif result is None:
                    break  # Zakończ aplikację
    
    except KeyboardInterrupt:
        logger.info("Przerwano przez użytkownika")
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd: {e}", exc_info=True)
    finally:
        # Zakończenie Pygame
        pygame.quit()
        logger.info("Aplikacja zakończona")

if __name__ == "__main__":
    # Obsługa parametru trybu testowego
    test_mode = "--test" in sys.argv
    if test_mode:
        logger.info("Uruchamianie w trybie testowym")
    
    try:
        main(test_mode)
    except Exception as e:
        logger.critical(f"Krytyczny błąd aplikacji: {e}", exc_info=True)
        sys.exit(1)