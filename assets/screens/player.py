import os
import sys
import math
import time
import pygame
import cairosvg
import io
import logging
import json
from services.shairport_listener import (
    get_current_track_info_shairport,
    get_active_state,
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
    
    # Początkowy stan
    last_title = last_artist = last_album = last_cover = None
    last_active_state = None

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
        current_active_state = get_active_state()
        
        # Aktualizuj ekran tylko jeśli coś się zmieniło
        if (title != last_title or artist != last_artist or 
            album != last_album or cover_path != last_cover or 
            current_active_state != last_active_state):

            if not any([title, artist, album]):
                title = " "
                artist = " "
                album = " "
            if not cover_path or not os.path.isfile(cover_path):
                cover_path = os.path.join(BASE_DIR, "assets", "images", "cover.png")

            draw_cover_art(screen, cover_path, WIDTH, HEIGHT)

            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            artist = truncate_text(artist)
            album = truncate_text(album)
            title = truncate_text(title)

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
            logger.debug(f"Active state (icon): {current_active_state}")
            if current_active_state:
                screen.blit(pause_icon, (CENTER_X - pause_icon.get_width() // 2, CENTER_Y - pause_icon.get_height() // 2))
            else:
                screen.blit(play_icon, (CENTER_X - play_icon.get_width() // 2, CENTER_Y - play_icon.get_height() // 2))

            pygame.display.flip()

            # Zapamiętaj aktualny stan
            last_title, last_artist, last_album, last_cover = title, artist, album, cover_path
            last_active_state = current_active_state

        clock.tick(30)

    pygame.quit()

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