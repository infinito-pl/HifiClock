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

def run_player_screen(screen, test_mode=False):
    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    SWIPE_THRESHOLD = 0.25
    start_y = None  # początkowa pozycja swipa

    clock = pygame.time.Clock()
    running = True

    WHITE      = (255, 255, 255)
    BLACK      = (0,   0,   0)
    SEMI_BLACK = (0,   0,   0, 128)
    BACKGROUND_COLOR = (30, 30, 30)

    font_regular_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold_path    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    if not os.path.isfile(font_regular_path):
        font_regular_path = pygame.font.get_default_font()
    if not os.path.isfile(font_bold_path):
        font_bold_path = pygame.font.get_default_font()

    font_artist = pygame.font.Font(font_bold_path, 50)
    font_album  = pygame.font.Font(font_regular_path, 30)
    font_title  = pygame.font.Font(font_regular_path, 50)

    # Załaduj ikony play/pause
    play_icon = load_and_render_svg(os.path.join(BASE_DIR, "assets", "icons", "btn_play.svg"), 158, 158)
    pause_icon = load_and_render_svg(os.path.join(BASE_DIR, "assets", "icons", "btn_pause.svg"), 158, 158)
    
    is_playing = False  # Zmienna do kontrolowania stanu odtwarzania

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.FINGERDOWN:
                start_y = event.y * HEIGHT
            elif event.type == pygame.FINGERUP and start_y is not None:
                end_y = event.y * HEIGHT
                delta_y = start_y - end_y  # Zmiana na odwrócony gest
                if delta_y > SWIPE_THRESHOLD:
                    pygame.event.clear()
                    return "clock"  # Przechodzimy do zegarka
                start_y = None

        screen.fill(BACKGROUND_COLOR)

        title, artist, album, cover_path = get_current_track_info_shairport()
        
        if not any([title, artist, album]):
            title = " "
            artist = " "
            album = " "
        if not cover_path or not os.path.isfile(cover_path):
            cover_path = os.path.join(BASE_DIR, "assets", "images", "cover.png")

        cover_image = pygame.image.load(cover_path)
        cover_image = pygame.transform.scale(cover_image, (WIDTH, HEIGHT))
        screen.blit(cover_image, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        artist = truncate_text(artist)
        album = truncate_text(album)
        title = truncate_text(title)

        # Sprawdzenie stanu odtwarzania (czy jest utwór odtwarzany)
      

        if artist:
            artist_surface = font_artist.render(artist, True, WHITE)
            screen.blit(artist_surface, (CENTER_X - artist_surface.get_width() // 2, CENTER_Y - 175))

        if album:
            album_surface = font_album.render(album, True, WHITE)
            screen.blit(album_surface, (CENTER_X - album_surface.get_width() // 2, CENTER_Y - 100))

        if title:
            title_surface = font_title.render(title, True, WHITE)
            screen.blit(title_surface, (CENTER_X - title_surface.get_width() // 2, CENTER_Y + 100))

        # Renderowanie ikony play/pause
        current_active_state = get_active_state()
        logger.debug(f"Active state (icon): {current_active_state}")
        if current_active_state:
            screen.blit(pause_icon, (CENTER_X - pause_icon.get_width() // 2, CENTER_Y - pause_icon.get_height() // 2))
        else:
            screen.blit(play_icon, (CENTER_X - play_icon.get_width() // 2, CENTER_Y - play_icon.get_height() // 2))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()