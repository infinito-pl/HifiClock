import os
import sys
import pygame
import logging
import threading
import signal
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import (
    get_current_track_info_shairport,
    active_state,
    should_switch_to_player_screen,
    should_switch_to_clock_screen,
    reset_switch_flags,
    read_shairport_metadata
)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Globalna zmienna do kontroli zamykania aplikacji
running = True

def signal_handler(signum, frame):
    """Obsługa sygnałów zamykania aplikacji."""
    global running
    logger.debug(f"Otrzymano sygnał {signum}")
    running = False
    # Rzucamy wyjątek KeyboardInterrupt, aby przerwać główną pętlę
    raise KeyboardInterrupt()

def start_shairport_listener():
    """Uruchamia listener Shairport w osobnym wątku."""
    thread = threading.Thread(target=read_shairport_metadata, daemon=True)
    thread.start()
    logger.debug("Shairport listener started in background thread")
    return thread

def main():
    global running
    
    # Rejestracja obsługi sygnałów
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)
    
    def cleanup():
        """Przywraca oryginalne obsługi sygnałów."""
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    pygame.init()
    pygame.mixer.quit() #Pygame nie blokuje karty muzycznej dla Shairport i Mopidy
    pygame.mouse.set_visible(False)
    
    # Ustawienie trybu pełnoekranowego
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_size()
    
    # Inicjalizacja zegara
    clock = pygame.time.Clock()
    
    # Uruchom listener Shairport w tle
    shairport_thread = start_shairport_listener()
    
    # Początkowy ekran
    current_screen = "clock"
    logger.debug(f"Początkowy ekran: {current_screen}")
    
    # Licznik do sprawdzania stanu odtwarzania
    check_counter = 0
    CHECK_INTERVAL = 15  # Sprawdzaj co 15 klatek (około 0.5 sekundy przy 30 FPS)
    
    try:
        while running:
            # Sprawdź stan odtwarzania co określony interwał
            check_counter += 1
            if check_counter >= CHECK_INTERVAL:
                check_counter = 0
                
                # Sprawdź czy należy przełączyć ekran
                if should_switch_to_player_screen() and current_screen == "clock":
                    logger.debug("=== Przełączanie na ekran odtwarzacza ===")
                    current_screen = "player"
                    reset_switch_flags()
                    logger.debug(f"Nowy ekran: {current_screen}")
                elif should_switch_to_clock_screen() and current_screen == "player":
                    logger.debug("=== Przełączanie na ekran zegara ===")
                    current_screen = "clock"
                    reset_switch_flags()
                    logger.debug(f"Nowy ekran: {current_screen}")
            
            # Uruchom odpowiedni ekran
            if current_screen == "clock":
                next_screen = run_clock_screen(screen)
            else:
                next_screen = run_player_screen(screen)
            
            # Jeśli ekran zwrócił następny ekran, przełącz
            if next_screen:
                logger.debug(f"Ekran zwrócił następny ekran: {next_screen}")
                current_screen = next_screen
                reset_switch_flags()  # Resetuj flagi przed przejściem do nowego ekranu
                logger.debug(f"Nowy ekran: {current_screen}")
            
            clock.tick(30)
            
    except KeyboardInterrupt:
        logger.debug("Otrzymano KeyboardInterrupt - zamykanie aplikacji")
    except Exception as e:
        logger.error(f"Błąd w głównej pętli: {e}")
    finally:
        logger.debug("Zamykanie aplikacji...")
        running = False
        cleanup()  # Przywróć oryginalne obsługi sygnałów
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()