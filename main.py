import os
import sys
import pygame
import threading
import logging
import time
from datetime import datetime
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import get_current_track_info_shairport, read_shairport_metadata

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Globalne zmienne dla metadanych
current_metadata = {
    'title': None,
    'artist': None,
    'album': None,
    'cover_path': None,
    'source': None,  # 'shairport' lub 'mopidy'
    'is_playing': False
}

def metadata_thread():
    """Wątek obsługujący odczyt metadanych z różnych źródeł."""
    logger.debug("Uruchamiam wątek metadanych")
    
    while True:
        try:
            # Sprawdzamy Shairport
            title, artist, album, cover_path = get_current_track_info_shairport()
            if title or artist or album:
                current_metadata.update({
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'cover_path': cover_path,
                    'source': 'shairport',
                    'is_playing': True
                })
                logger.debug(f"Zaktualizowano metadane z Shairport: {title} - {artist}")
            
            # Tutaj później dodamy obsługę Mopidy
            
            time.sleep(1)  # Sprawdzamy co sekundę
            
        except Exception as e:
            logger.error(f"Błąd w wątku metadanych: {e}")
            time.sleep(1)

def main():
    # Inicjalizacja Pygame
    pygame.init()
    pygame.display.init()
    pygame.font.init()
    
    # Pobierz rozmiar ekranu
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    
    # Utwórz okno w trybie pełnoekranowym
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("HifiClock")
    
    # Uruchom wątek metadanych
    metadata_thread = threading.Thread(target=metadata_thread, daemon=True)
    metadata_thread.start()
    
    # Główna pętla aplikacji
    current_screen = "clock"
    running = True
    
    while running:
        try:
            # Sprawdzamy czy mamy aktywne odtwarzanie
            if current_metadata['is_playing'] and current_screen == "clock":
                logger.debug("Wykryto odtwarzanie, przełączam na ekran odtwarzacza")
                current_screen = "player"
            elif not current_metadata['is_playing'] and current_screen == "player":
                logger.debug("Brak odtwarzania, przełączam na ekran zegara")
                current_screen = "clock"
            
            # Uruchom odpowiedni ekran
            if current_screen == "clock":
                result = run_clock_screen(screen)
                if result == "player":
                    current_screen = "player"
            else:
                result = run_player_screen(screen, metadata=current_metadata)
                if result == "clock":
                    current_screen = "clock"
            
            # Obsługa zdarzeń
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
        except Exception as e:
            logger.error(f"Błąd w głównej pętli: {e}")
            time.sleep(1)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()