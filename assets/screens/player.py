import os
import sys
import math
import time
import pygame
import cairosvg
import io
import logging
import json
import tempfile
import subprocess
from PIL import Image, ImageDraw
from services.shairport_listener import get_current_track_info_shairport
from utils.svg_loader import load_and_render_svg
from services.shairport_active import get_active_state

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

# Ścieżka bazowa projektu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def truncate_text(text, max_length):
    """
    Skraca tekst do określonej długości, dodając '...' jeśli jest zbyt długi.
    
    :param text: Tekst do skrócenia
    :param max_length: Maksymalna długość tekstu
    :return: Skrócony tekst
    """
    if text and len(text) > max_length:
        return text[:max_length - 3] + '...'
    return text

# Zdefiniuj funkcję do ładowania i rysowania SVG
def load_and_render_svg(svg_path, width, height):
    """
    Ładuje plik SVG i renderuje go do powierzchni Pygame.
    
    :param svg_path: Ścieżka do pliku SVG
    :param width: Szerokość docelowa
    :param height: Wysokość docelowa
    :return: Powierzchnia Pygame z wyrenderowanym SVG
    """
    try:
        # Używamy podprocesu do konwersji SVG na PNG
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_png_path = tmp_file.name
        
        cmd = ['convert', '-background', 'none', '-size', f'{width}x{height}', svg_path, tmp_png_path]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ładowanie przekonwertowanego pliku PNG
        image = pygame.image.load(tmp_png_path)
        os.unlink(tmp_png_path)  # Usunięcie pliku tymczasowego
        
        return image
    except Exception as e:
        logger.error(f"Błąd podczas ładowania SVG {svg_path}: {e}")
        # Utworzenie przezroczystej powierzchni z krzyżykiem jako fallback
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.line(surface, (255, 0, 0), (0, 0), (width, height), 2)
        pygame.draw.line(surface, (255, 0, 0), (0, height), (width, 0), 2)
        return surface

# Zmniejszenie częstotliwości sprawdzania aktywności
ACTIVITY_CHECK_INTERVAL = 60  # Sprawdzanie co 60 sekund zamiast 10
LAST_ACTIVITY_CHECK = 0

logger = logging.getLogger(__name__)

def run_player_screen(screen, test_mode=False, metadata=None):
    """
    Uruchamia ekran odtwarzacza muzyki.
    
    Args:
        screen: Powierzchnia pygame do rysowania
        test_mode: Czy aplikacja jest w trybie testowym
        metadata: Słownik z metadanymi: title, artist, album, cover_path, is_playing
        
    Returns:
        str: "clock" jeśli użytkownik chce wrócić do ekranu zegara
        None: jeśli użytkownik chce zamknąć aplikację
    """
    global LAST_ACTIVITY_CHECK
    
    logger.debug("Uruchamianie ekranu odtwarzacza z metadanymi")
    
    # Jeśli nie otrzymaliśmy metadanych, spróbujmy pobrać je lokalnie jako backup
    if not metadata or (metadata and not metadata.get('title') and not metadata.get('artist')):
        logger.debug("Brak metadanych z main.py, próba pobrania lokalnie")
        try:
            from services.shairport_listener import get_current_track_info_shairport
            track_info = get_current_track_info_shairport()
            if track_info:
                title, artist, album, cover_path = track_info
                metadata = {
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'cover_path': cover_path,
                    'is_playing': True if (title and artist) else False
                }
                logger.debug(f"Pobrano lokalne metadane: {title} - {artist}")
        except Exception as e:
            logger.error(f"Błąd podczas pobierania lokalnych metadanych: {e}")
    
    # Ustawienia ekranu
    width, height = screen.get_size()
    
    # Kolory
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 100)
    
    # Ścieżki czcionek
    font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
    regular_font_path = os.path.join(font_dir, "Roboto-Regular.ttf")
    bold_font_path = os.path.join(font_dir, "Roboto-Bold.ttf")
    
    # Załaduj czcionki
    try:
        title_font = pygame.font.Font(bold_font_path, 36)
        artist_font = pygame.font.Font(regular_font_path, 30)
        album_font = pygame.font.Font(regular_font_path, 24)
    except Exception as e:
        logger.error(f"Błąd podczas ładowania czcionek: {e}")
        # Fallback do czcionek systemowych
        title_font = pygame.font.SysFont("Arial", 36, bold=True)
        artist_font = pygame.font.SysFont("Arial", 30)
        album_font = pygame.font.SysFont("Arial", 24)
    
    # Załaduj domyślną okładkę
    default_cover_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "default_cover.png")
    try:
        default_cover = pygame.image.load(default_cover_path)
        default_cover = pygame.transform.scale(default_cover, (300, 300))
    except Exception as e:
        logger.error(f"Błąd podczas ładowania domyślnej okładki: {e}")
        # Tworzenie pustej okładki
        default_cover = pygame.Surface((300, 300))
        default_cover.fill(GRAY)
    
    # Inicjalizacja zmiennych gestów
    start_y = None
    SWIPE_THRESHOLD = 0.25
    
    # Główna pętla
    running = True
    
    while running:
        # Sprawdź aktywność co określony czas
        current_time = time.time()
        if current_time - LAST_ACTIVITY_CHECK > ACTIVITY_CHECK_INTERVAL:
            logger.debug("Sprawdzanie aktywności odtwarzania")
            LAST_ACTIVITY_CHECK = current_time
            
            # Sprawdź czy mamy ważne metadane
            if metadata and metadata.get('title') and metadata.get('artist'):
                logger.debug(f"Aktualne metadane: {metadata.get('title')} - {metadata.get('artist')}")
                is_active = metadata.get('is_playing', False)
                if not is_active:
                    logger.debug("Brak aktywnego odtwarzania, powrót do zegara")
                    return "clock"
            else:
                logger.debug("Brak ważnych metadanych, sprawdzanie aktywności")
                # Tutaj można dodać alternatywne sprawdzenie aktywności
        
        # Pobierz okładkę z metadanych lub użyj domyślnej
        if metadata and metadata.get('cover_path'):
            try:
                cover_path = metadata.get('cover_path')
                album_cover = pygame.image.load(cover_path)
                album_cover = pygame.transform.scale(album_cover, (300, 300))
            except Exception as e:
                logger.error(f"Błąd podczas ładowania okładki: {e}")
                album_cover = default_cover
        else:
            album_cover = default_cover
        
        # Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # Obsługa klawiszy
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_SPACE:
                    return "clock"
            
            # Obsługa gestów dotykowych
            elif event.type == pygame.FINGERDOWN:
                start_y = event.y
                logger.debug(f"Początek gestu: {start_y}")
            
            elif event.type == pygame.FINGERUP and start_y is not None:
                end_y = event.y
                logger.debug(f"Koniec gestu: {end_y}")
                
                # Gest w górę - przejście do zegara
                if start_y - end_y > SWIPE_THRESHOLD:  # Gest w górę (od dołu do góry ekranu)
                    logger.debug(f"Wykryto gest w górę: {start_y} -> {end_y}, powrót do zegara")
                    return "clock"
                
                start_y = None
        
        # Czyszczenie ekranu
        screen.fill(BLACK)
        
        # Rysowanie okładki
        cover_rect = album_cover.get_rect(midtop=(width/2, 50))
        screen.blit(album_cover, cover_rect)
        
        # Rysowanie informacji o utworze
        y_position = cover_rect.bottom + 20
        
        # Tytuł utworu
        if metadata and metadata.get('title'):
            title_text = metadata.get('title')
            # Zawijanie długich tytułów
            wrapped_title = textwrap.wrap(title_text, width=30)
            for line in wrapped_title[:2]:  # Maksymalnie 2 linie tytułu
                title_surface = title_font.render(line, True, WHITE)
                title_rect = title_surface.get_rect(midtop=(width/2, y_position))
                screen.blit(title_surface, title_rect)
                y_position += title_surface.get_height() + 5
        
        # Artysta
        if metadata and metadata.get('artist'):
            artist_text = metadata.get('artist')
            artist_surface = artist_font.render(artist_text, True, WHITE)
            artist_rect = artist_surface.get_rect(midtop=(width/2, y_position))
            screen.blit(artist_surface, artist_rect)
            y_position += artist_surface.get_height() + 5
        
        # Album
        if metadata and metadata.get('album'):
            album_text = metadata.get('album')
            album_surface = album_font.render(album_text, True, GRAY)
            album_rect = album_surface.get_rect(midtop=(width/2, y_position))
            screen.blit(album_surface, album_rect)
        
        # Aktualizuj ekran
        pygame.display.flip()
        
        # Limit FPS
        time.sleep(0.03)  # ~30fps
    
    return None

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