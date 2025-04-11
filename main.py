import os
import sys
import pygame
import logging
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import (
    get_current_track_info_shairport,
    active_state,
    should_switch_to_player_screen,
    should_switch_to_clock_screen,
    reset_switch_flags
)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def main():
    pygame.init()
    pygame.mixer.quit()
    pygame.mouse.set_visible(False)
    
    # Ustawienie trybu pełnoekranowego
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_size()
    
    # Inicjalizacja zegara
    clock = pygame.time.Clock()
    
    # Początkowy ekran
    current_screen = "clock"
    
    # Licznik do sprawdzania stanu odtwarzania
    check_counter = 0
    CHECK_INTERVAL = 30  # Sprawdzaj co 30 klatek (około 1 sekunda przy 30 FPS)
    
    while True:
        try:
            # Sprawdź stan odtwarzania co określony interwał
            check_counter += 1
            if check_counter >= CHECK_INTERVAL:
                check_counter = 0
                # Pobierz aktualne informacje o utworze
                track_info = get_current_track_info_shairport()
                logger.debug(f"Stan odtwarzania: {active_state}, Track info: {track_info}")
                
                # Przełącz ekran na podstawie stanu odtwarzania
                if active_state and current_screen == "clock":
                    logger.debug("Wykryto odtwarzanie - przełączanie na ekran odtwarzacza")
                    current_screen = "player"
                elif not active_state and current_screen == "player":
                    logger.debug("Brak odtwarzania - przełączanie na ekran zegara")
                    current_screen = "clock"
            
            # Uruchom odpowiedni ekran
            if current_screen == "clock":
                next_screen = run_clock_screen(screen)
            else:
                next_screen = run_player_screen(screen)
            
            # Jeśli ekran zwrócił następny ekran, przełącz
            if next_screen:
                logger.debug(f"Przełączanie na ekran: {next_screen}")
                current_screen = next_screen
            
            clock.tick(30)
            
        except Exception as e:
            logger.error(f"Błąd w głównej pętli: {e}")
            pygame.quit()
            sys.exit(1)

if __name__ == "__main__":
    main()