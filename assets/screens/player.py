import os
import sys
import math
import time
import pygame
import cairosvg
import io
from services.shairport_listener import read_metadata

try:
    from services.metadata_shairport import get_current_track_info_shairport
except ImportError:
    def get_current_track_info_shairport():
        return (None, None, None, None)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_player_screen(screen, test_mode=False):
    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    clock = pygame.time.Clock()
    running = True

    WHITE      = (255, 255, 255)
    BLACK      = (0,   0,   0)
    SEMI_BLACK = (0,   0,   0, 128)

    font_regular_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold_path    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    if not os.path.isfile(font_regular_path):
        font_regular_path = pygame.font.get_default_font()
    if not os.path.isfile(font_bold_path):
        font_bold_path = pygame.font.get_default_font()

    font_regular = pygame.font.Font(font_regular_path, 24)
    font_bold    = pygame.font.Font(font_bold_path, 30)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)

        title, artist, album, cover_path, updated = get_current_track_info_shairport()

        if title:
            text_surface = font_bold.render(title, True, WHITE)
            screen.blit(text_surface, (CENTER_X - text_surface.get_width() // 2, 100))

        if artist:
            text_surface = font_regular.render(artist, True, WHITE)
            screen.blit(text_surface, (CENTER_X - text_surface.get_width() // 2, 150))

        if album:
            text_surface = font_regular.render(album, True, WHITE)
            screen.blit(text_surface, (CENTER_X - text_surface.get_width() // 2, 200))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()