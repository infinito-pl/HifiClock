import os
import sys
import math
import time
import pygame
import cairosvg
import io
from services.shairport_listener import read_shairport_metadata

try:
    from services.metadata_shairport import get_current_track_info_shairport
except ImportError:
    def get_current_track_info_shairport():
        return (None, None, None, None)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def truncate_text(text, max_length=30):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."

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

        if artist:
            artist_surface = font_artist.render(artist, True, WHITE)
            screen.blit(artist_surface, (CENTER_X - artist_surface.get_width() // 2, CENTER_Y - 175))

        if album:
            album_surface = font_album.render(album, True, WHITE)
            screen.blit(album_surface, (CENTER_X - album_surface.get_width() // 2, CENTER_Y - 100))

        if title:
            title_surface = font_title.render(title, True, WHITE)
            screen.blit(title_surface, (CENTER_X - title_surface.get_width() // 2, CENTER_Y + 100))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()