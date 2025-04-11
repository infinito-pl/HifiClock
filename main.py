import os
import sys
import pygame
import logging
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import (
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
    pygame.mixer.quit()  # Wyłączamy mixer, aby nie blokować karty dźwiękowej
    pygame.display.init()
    pygame.mouse.set_visible(False)
    
    # Ustawienie trybu pełnoekranowego
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_size()
    
    # Inicjalizacja zegara
    clock = pygame.time.Clock()
    
    # Początkowy ekran
    current_screen = "clock"
    
    while True:
        try:
            # Sprawdź czy należy przełączyć ekran
            if should_switch_to_player_screen() and current_screen == "clock":
                logger.debug("Przełączanie na ekran odtwarzacza")
                current_screen = "player"
                reset_switch_flags()
            elif should_switch_to_clock_screen() and current_screen == "player":
                logger.debug("Przełączanie na ekran zegara")
                current_screen = "clock"
                reset_switch_flags()
            
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