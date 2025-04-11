import os
import sys
import math
import time
import pygame
import cairosvg
import io
import logging
import json
from config import COLORS, FONTS, ICONS, DEFAULT_COVER, SCREEN_WIDTH, SCREEN_HEIGHT
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

def truncate_text(text, max_length=30):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."

# Zdefiniuj funkcję do ładowania i rysowania SVG
def load_and_render_svg(file_path, width, height):
    svg_data = cairosvg.svg2png(url=file_path)
    icon_image = pygame.image.load(io.BytesIO(svg_data))
    icon_image = pygame.transform.scale(icon_image, (width, height))
    return icon_image

class PlayerScreen(BaseScreen):
    def __init__(self, screen):
        super().__init__(screen)
        self.font_artist = pygame.font.Font(FONTS["REGULAR"], 36)
        self.font_album = pygame.font.Font(FONTS["REGULAR"], 32)
        self.font_title = pygame.font.Font(FONTS["BOLD"], 48)
        self.play_icon = self.load_icon(ICONS["PLAY"])
        self.pause_icon = self.load_icon(ICONS["PAUSE"])
        self.cover_image = None
        self.current_metadata = None

    def load_icon(self, icon_path):
        """Ładuje ikonę SVG i konwertuje ją na powierzchnię Pygame."""
        try:
            icon = pygame.image.load(icon_path)
            icon = pygame.transform.scale(icon, (50, 50))
            return icon
        except Exception as e:
            logger.error(f"Błąd ładowania ikony {icon_path}: {e}")
            return None

    def load_cover(self, cover_path):
        """Ładuje okładkę albumu."""
        try:
            if cover_path and os.path.exists(cover_path):
                self.cover_image = pygame.image.load(cover_path)
                self.cover_image = pygame.transform.scale(self.cover_image, (300, 300))
            else:
                self.cover_image = pygame.image.load(DEFAULT_COVER)
                self.cover_image = pygame.transform.scale(self.cover_image, (300, 300))
        except Exception as e:
            logger.error(f"Błąd ładowania okładki {cover_path}: {e}")
            self.cover_image = pygame.image.load(DEFAULT_COVER)
            self.cover_image = pygame.transform.scale(self.cover_image, (300, 300))

    def update(self):
        """Aktualizuje stan ekranu."""
        title, artist, album, cover_path = get_current_track_info()
        if (title, artist, album, cover_path) != self.current_metadata:
            self.current_metadata = (title, artist, album, cover_path)
            self.load_cover(cover_path)

    def draw(self):
        """Rysuje zawartość ekranu."""
        super().draw()
        
        if self.cover_image:
            cover_rect = self.cover_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(self.cover_image, cover_rect)
        
        if self.current_metadata:
            title, artist, album, _ = self.current_metadata
            
            if artist:
                artist_surface = self.font_artist.render(artist, True, COLORS["WHITE"])
                artist_rect = artist_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
                self.screen.blit(artist_surface, artist_rect)
            
            if album:
                album_surface = self.font_album.render(album, True, COLORS["LIGHT_GRAY"])
                album_rect = album_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
                self.screen.blit(album_surface, album_rect)
            
            if title:
                title_surface = self.font_title.render(title, True, COLORS["WHITE"])
                title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 220))
                self.screen.blit(title_surface, title_rect)
        
        # Rysuj ikonę play/pause
        icon = self.play_icon if self.current_metadata and self.current_metadata[3] else self.pause_icon
        if icon:
            icon_rect = icon.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 270))
            self.screen.blit(icon, icon_rect)

    def run(self):
        """Główna pętla ekranu odtwarzacza."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.FINGERDOWN:
                    self.start_x = event.x * SCREEN_WIDTH
                    self.start_y = event.y * SCREEN_HEIGHT
                elif event.type == pygame.FINGERUP:
                    end_x = event.x * SCREEN_WIDTH
                    end_y = event.y * SCREEN_HEIGHT
                    dx = end_x - self.start_x
                    dy = end_y - self.start_y
                    
                    # Sprawdź gest przesunięcia w górę
                    if abs(dy) > 50 and dy < 0 and abs(dx) < 50:
                        return "clock"
            
            self.update()
            self.draw()
            pygame.display.flip()
            pygame.time.Clock().tick(60)

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
        default_cover = pygame.image.load(DEFAULT_COVER)
        default_cover = pygame.transform.scale(default_cover, (screen_width, screen_height))
        default_cover.set_alpha(int(0.4 * 255))  # To samo opacity dla domyślnej okładki
        screen.blit(default_cover, (0, 0))