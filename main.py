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

def start_shairport_listener():
    """Uruchamia listener Shairport w osobnym wątku."""
    thread = threading.Thread(target=read_shairport_metadata, daemon=True)
    thread.start()
    logger.debug("Shairport listener started in background thread")

def main():
    # Inicjalizacja Pygame
    pygame.init()
    pygame.mixer.quit()  # Wyłączamy mixer, aby nie blokować karty dźwiękowej
    pygame.display.init()
    pygame.mouse.set_visible(False)

    # Pobierz rozmiar ekranu
    screen_info = pygame.display.Info()
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h

    # Utwórz okno pełnoekranowe
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("HifiClock")

    # Uruchom listener Shairport w tle
    start_shairport_listener()

    # Początkowy ekran
    current_screen = "clock"

    try:
        while True:
            # Sprawdź czy należy przełączyć ekran
            if should_switch_to_player_screen() and current_screen == "clock":
                logger.debug("Switching to player screen")
                current_screen = "player"
                reset_switch_flags()
            elif should_switch_to_clock_screen() and current_screen == "player":
                logger.debug("Switching to clock screen")
                current_screen = "clock"
                reset_switch_flags()

            # Uruchom odpowiedni ekran
            if current_screen == "clock":
                result = run_clock_screen(screen)
                if result == "player":
                    current_screen = "player"
                    reset_switch_flags()
            else:
                result = run_player_screen(screen)
                if result == "clock":
                    current_screen = "clock"
                    reset_switch_flags()

    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()