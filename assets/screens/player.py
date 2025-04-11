import os
import sys
import math
import time
import pygame
import cairosvg
import io
import logging
import json
from services.shairport_listener import read_shairport_metadata
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

STATE_FILE = "/tmp/shairport_state.json"

def get_active_state():
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            return state.get("active_state", False)
    except (FileNotFoundError, json.JSONDecodeError):
        return False

try:
    from services.shairport_listener import get_current_track_info_shairport
except ImportError:
    def get_current_track_info_shairport():
        return (None, None, None, None)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def truncate_text(text, max_length=30):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."

# Zdefiniuj funkcję do ładowania i rysowania SVG
def load_and_render_svg(file_path, width, height):
    svg_data = cairosvg.svg2png(url=file_path)
    icon_image = pygame.image.load(io.BytesIO(svg_data))
    icon_image = pygame.transform.scale(icon_image, (width, height))
    return icon_image

def run_player_screen(screen, metadata=None):
    """Ekran odtwarzacza muzyki."""
    logger.debug("Uruchamiam ekran odtwarzacza")
    
    # Pobierz rozmiar ekranu
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Załaduj ikony
    play_icon = pygame.image.load("assets/icons/play.svg")
    pause_icon = pygame.image.load("assets/icons/pause.svg")
    
    # Skaluj ikony do odpowiedniego rozmiaru
    icon_size = int(screen_height * 0.1)
    play_icon = pygame.transform.scale(play_icon, (icon_size, icon_size))
    pause_icon = pygame.transform.scale(pause_icon, (icon_size, icon_size))
    
    # Inicjalizacja zmiennych dla gestów
    start_y = None
    SWIPE_THRESHOLD = 0.25  # 25% wysokości ekranu
    
    # Główna pętla ekranu odtwarzacza
    running = True
    while running:
        try:
            # Sprawdź czy mamy metadane
            if metadata and metadata.get('title') and metadata.get('artist'):
                title = metadata['title']
                artist = metadata['artist']
                album = metadata.get('album', '')
                cover_path = metadata.get('cover_path')
                is_playing = metadata.get('is_playing', False)
                
                # Wyświetl informacje o utworze
                logger.debug(f"Wyświetlam utwór: {title} - {artist}")
                
                # Wyczyść ekran
                screen.fill((0, 0, 0))
                
                # Wyświetl okładkę jeśli jest dostępna
                if cover_path and os.path.exists(cover_path):
                    try:
                        cover = pygame.image.load(cover_path)
                        cover = pygame.transform.scale(cover, (screen_height, screen_height))
                        screen.blit(cover, (0, 0))
                    except Exception as e:
                        logger.error(f"Błąd ładowania okładki: {e}")
                
                # Wyświetl tytuł i wykonawcę
                font = pygame.font.Font(None, int(screen_height * 0.1))
                title_text = font.render(title, True, (255, 255, 255))
                artist_text = font.render(artist, True, (200, 200, 200))
                
                # Wyśrodkuj tekst
                title_rect = title_text.get_rect(center=(screen_width/2, screen_height*0.3))
                artist_rect = artist_text.get_rect(center=(screen_width/2, screen_height*0.4))
                
                screen.blit(title_text, title_rect)
                screen.blit(artist_text, artist_rect)
                
                # Wyświetl ikonę play/pause
                icon = pause_icon if is_playing else play_icon
                icon_rect = icon.get_rect(center=(screen_width/2, screen_height*0.7))
                screen.blit(icon, icon_rect)
                
            else:
                # Jeśli nie ma metadanych, wróć do zegara
                logger.debug("Brak metadanych, wracam do zegara")
                return "clock"
            
            # Obsługa zdarzeń
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                elif event.type == pygame.FINGERDOWN:
                    start_y = event.y * screen_height
                    logger.debug(f"FINGERDOWN  x={event.x:.3f}, y={event.y:.3f}")
                
                elif event.type == pygame.FINGERUP and start_y is not None:
                    end_y = event.y * screen_height
                    delta_y = end_y - start_y
                    logger.debug(f"FINGERUP    x={event.x:.3f}, y={event.y:.3f}")
                    logger.debug(f" FINGER swipe delta_y={delta_y:.2f}, start_y={start_y:.2f}, end_y={end_y:.2f}")
                    
                    if abs(delta_y) > screen_height * SWIPE_THRESHOLD:
                        if delta_y < 0:  # Przesunięcie w górę
                            logger.debug(" SWIPE FINGER => switch to clock")
                            return "clock"
                    
                    start_y = None
            
            pygame.display.flip()
            pygame.time.delay(30)  # 30 FPS
            
        except Exception as e:
            logger.error(f"Błąd w ekranie odtwarzacza: {e}")
            return "clock"
    
    return "clock"

def draw_cover_art(screen, cover_path, screen_width, screen_height):
    try:
        if cover_path and os.path.exists(cover_path):
            cover = pygame.image.load(cover_path)
            cover = pygame.transform.scale(cover, (screen_width, screen_height))
            cover.set_alpha(int(0.4 * 255))  # Zmniejszamy opacity z 0.5 do 0.4
            screen.blit(cover, (0, 0))
    except Exception as e:
        logger.error(f"Error loading cover art: {e}")
        # W przypadku błędu, wyświetl domyślną okładkę
        default_cover = pygame.image.load(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images", "cover.png"))
        default_cover = pygame.transform.scale(default_cover, (screen_width, screen_height))
        default_cover.set_alpha(int(0.4 * 255))  # To samo opacity dla domyślnej okładki
        screen.blit(default_cover, (0, 0))