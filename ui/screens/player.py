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
from config import COLORS, FONTS, ICONS, DEFAULT_COVER
from ui.screens.base import BaseScreen
from utils.logging import logger
from services.metadata.shairport import get_current_track_info

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

class PlayerScreen(BaseScreen):
    def __init__(self, screen, test_mode=False):
        super().__init__(screen, test_mode)
        self.font_artist = pygame.font.Font(FONTS['BOLD'], 50)
        self.font_album = pygame.font.Font(FONTS['REGULAR'], 30)
        self.font_title = pygame.font.Font(FONTS['REGULAR'], 50)
        
        # Załaduj ikony
        self.play_icon = self.load_svg_icon(ICONS['PLAY'], 158, 158)
        self.pause_icon = self.load_svg_icon(ICONS['PAUSE'], 158, 158)
        
        # Inicjalizacja metadanych
        self.title = self.artist = self.album = None
        self.cover_path = DEFAULT_COVER
        self.cover_image = None
        self.is_playing = False

    def load_svg_icon(self, file_path, width, height):
        """Ładuje ikonę SVG."""
        try:
            svg_data = cairosvg.svg2png(url=file_path)
            icon_image = pygame.image.load(io.BytesIO(svg_data))
            return pygame.transform.scale(icon_image, (width, height))
        except Exception as e:
            logger.error(f"Błąd ładowania ikony SVG: {e}")
            return None

    def load_cover(self):
        """Ładuje okładkę utworu."""
        try:
            if self.cover_path and self.cover_path != DEFAULT_COVER:
                self.cover_image = pygame.image.load(self.cover_path)
                self.cover_image = pygame.transform.scale(self.cover_image, (400, 400))
            else:
                self.cover_image = pygame.image.load(DEFAULT_COVER)
                self.cover_image = pygame.transform.scale(self.cover_image, (400, 400))
        except Exception as e:
            logger.error(f"Błąd ładowania okładki: {e}")
            self.cover_image = pygame.image.load(DEFAULT_COVER)
            self.cover_image = pygame.transform.scale(self.cover_image, (400, 400))

    def update(self):
        """Aktualizuje stan ekranu."""
        # Pobierz aktualne metadane
        title, artist, album, cover_path = get_current_track_info()
        
        # Sprawdź czy metadane się zmieniły
        if (title != self.title or artist != self.artist or 
            album != self.album or cover_path != self.cover_path):
            self.title = title
            self.artist = artist
            self.album = album
            self.cover_path = cover_path
            self.load_cover()

    def draw(self):
        """Rysuje ekran odtwarzacza."""
        super().draw()
        
        # Rysuj okładkę
        if self.cover_image:
            cover_rect = self.cover_image.get_rect(center=(self.width // 2, self.height // 2 - 100))
            self.screen.blit(self.cover_image, cover_rect)
        
        # Rysuj metadane
        if self.artist:
            artist_text = self.font_artist.render(self.artist, True, COLORS['WHITE'])
            artist_rect = artist_text.get_rect(center=(self.width // 2, self.height // 2 + 150))
            self.screen.blit(artist_text, artist_rect)
        
        if self.title:
            title_text = self.font_title.render(self.title, True, COLORS['WHITE'])
            title_rect = title_text.get_rect(center=(self.width // 2, self.height // 2 + 200))
            self.screen.blit(title_text, title_rect)
        
        if self.album:
            album_text = self.font_album.render(self.album, True, COLORS['WHITE'])
            album_rect = album_text.get_rect(center=(self.width // 2, self.height // 2 + 250))
            self.screen.blit(album_text, album_rect)
        
        # Rysuj ikonę play/pause
        icon = self.play_icon if not self.is_playing else self.pause_icon
        if icon:
            icon_rect = icon.get_rect(center=(self.width // 2, self.height // 2 + 300))
            self.screen.blit(icon, icon_rect)

    def run(self):
        """Uruchamia ekran odtwarzacza."""
        result = super().run()
        if result == "swipe_up":
            return "clock"
        return result

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