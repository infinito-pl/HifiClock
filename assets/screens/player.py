# player.py

import os
import sys
import math
import time
import pygame
import cairosvg
import io
from services.metadata_shairport import get_current_track_info_shairport

# Ładowanie modułu do metadanych Shairport. 
# Jeśli nie istnieje, po prostu mamy fallback (None, None, None, None).
try:
    from services.metadata_shairport import get_current_track_info_shairport
except ImportError:
    def get_current_track_info_shairport():
        return (None, None, None, None)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_player_screen(screen, test_mode=False):
    """
    Ekran odtwarzacza z layoutem:
      - Tło z okładką (50% opacity).
      - Pierścień postępu (arc) – start w godz.12, do 360*progress.
      - 3 przyciski: Prev, Play/Pause, Next (center).
      - Teksty: Artist (~y= -175), Album (~y= -120), Title (~y= +120).
      - Gest przejścia do 'clock': swipe up (dotyk) albo scroll w górę (test).
    """

    # Konfiguracja okna (width=height=800)
    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    clock = pygame.time.Clock()
    running = True

    # Kolory
    WHITE      = (255, 255, 255)
    BLACK      = (0,   0,   0)
    SEMI_BLACK = (0,   0,   0, 128)  # 50% alpha

    # Czcionki
    font_regular_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold_path    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_artist = pygame.font.Font(font_bold_path,  50)  # Wykonawca
    font_album  = pygame.font.Font(font_regular_path, 36)
    font_title  = pygame.font.Font(font_regular_path, 50)

    # Funkcja ładująca .svg → .png → surface
    def load_svg_button(filename, width=158, height=158):
        full_path = os.path.join(BASE_DIR, "assets", "icons", filename)
        if not os.path.exists(full_path):
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255,0,0), (0,0,width,height), 5)
            return surf
        try:
            with open(full_path, "rb") as f:
                svg_data = f.read()
            png_data = cairosvg.svg2png(
                bytestring=svg_data,
                output_width=width,
                output_height=height
            )
            button_surf = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
            return button_surf
        except Exception as e:
            print("[player] Nie udało się załadować ikony:", filename, e)
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255,0,0), (0,0,width,height), 5)
            return surf

    # Ładujemy ikony
    btn_prev_icon  = load_svg_button("btn_prev.svg")
    btn_next_icon  = load_svg_button("btn_next.svg")
    btn_play_icon  = load_svg_button("btn_play.svg")
    btn_pause_icon = load_svg_button("btn_pause.svg")

    # Rozmieszczenie przycisków
    btn_size = 158
    gap      = 40
    total_w  = btn_size*3 + gap*2
    start_x  = (WIDTH - total_w) // 2
    base_y   = (HEIGHT - btn_size) // 2

    rect_prev = pygame.Rect(start_x,               base_y, btn_size, btn_size)
    rect_play = pygame.Rect(start_x+btn_size+gap,  base_y, btn_size, btn_size)
    rect_next = pygame.Rect(start_x+2*(btn_size+gap), base_y, btn_size, btn_size)

    # Domyślna okładka
    default_cover_path = os.path.join(BASE_DIR, "assets", "images", "cover.png")

    # Sterowanie odtwarzaniem (dla testu)
    is_playing = True
    def current_play_button():
        return btn_pause_icon if is_playing else btn_play_icon

    # Parametry pierścienia
    RING_WIDTH  = 16
    RING_RADIUS = 380

    # Postęp testowy – docelowo można wczytywać z metadanych 'prgr'
    track_progress = 0.3

    # Obsługa gestów
    start_y = None
    # W trybie normalnym – finger swipe up => clock
    # W trybie test – scroll up => clock

    current_title = "Unknown Track"
    current_artist = "Unknown Artist"
    current_album = "Unknown Album"
    current_cover = os.path.join(BASE_DIR, "assets", "images", "cover.png")
    last_metadata = (None, None, None, None)

    while running:
        # Aktualizacja metadanych z Shairport
        title, artist, album, cover_path = get_current_track_info_shairport()
        if (title, artist, album, cover_path) != last_metadata:
            print(f'[DEBUG] track info: {title}, {artist}, {album}, {cover_path}')
            if title:  current_title = title
            if artist: current_artist = artist
            if album:  current_album = album
            if cover_path and os.path.exists(cover_path):
                current_cover = cover_path
            last_metadata = (title, artist, album, cover_path)

        # Zdarzenia
        for event in pygame.event.get():
            #print("[player debug] event:", event)

            if event.type == pygame.QUIT:
                running = False

            if test_mode:
                # scroll w górę => powrót do clock
                if event.type == pygame.MOUSEWHEEL and event.y > 0:
                    pygame.event.clear()
                    return "clock"
            else:
                # dotyk: swipe up => clock
                if event.type == pygame.FINGERDOWN:
                    start_y = event.y
                elif event.type == pygame.FINGERUP and start_y is not None:
                    end_y = event.y
                    delta_y = start_y - end_y
                    if delta_y > 0.25:  # ~25% okna
                        pygame.event.clear()
                        return "clock"
                    start_y = None

            if event.type == pygame.MOUSEBUTTONUP:
                # Wersja testowa: klik w przyciski
                mx, my = event.pos
                if rect_prev.collidepoint(mx, my):
                    print("[player] Prev pressed!")
                elif rect_play.collidepoint(mx, my):
                    print("[player] Play/Pause pressed!")
                    is_playing = not is_playing
                elif rect_next.collidepoint(mx, my):
                    print("[player] Next pressed!")

        # Rysowanie tła
        screen.fill(BLACK)

        # Okładka z 50% overlay
        try:
            cover_img = pygame.image.load(current_cover).convert()
            cover_img = pygame.transform.smoothscale(cover_img, (WIDTH, HEIGHT))
            cover_surf = cover_img.copy()

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(SEMI_BLACK)
            cover_surf.blit(overlay, (0,0))
            screen.blit(cover_surf, (0,0))
        except:
            pass

        # Pierścień postępu (arc)
        ring_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        color_ring = (255, 255, 255, 128)

        start_angle = -90
        end_angle   = start_angle + 360 * track_progress

        rect_arc = (
            CENTER_X - RING_RADIUS,
            CENTER_Y - RING_RADIUS,
            RING_RADIUS * 2,
            RING_RADIUS * 2
        )
        pygame.draw.arc(
            ring_surf,
            color_ring,
            rect_arc,
            math.radians(start_angle),
            math.radians(end_angle),
            RING_WIDTH
        )
        screen.blit(ring_surf, (0,0))

        # Teksty
        # W/g Twojego layoutu:
        # - artist ~ y=center-175
        # - album  ~ y=center-120
        # - title  ~ y=center+120
        performer_surf = font_artist.render(current_artist, True, WHITE)
        album_surf     = font_album.render(current_album.upper(), True, WHITE)
        title_surf     = font_title.render(current_title, True, WHITE)

        screen.blit(performer_surf, performer_surf.get_rect(center=(CENTER_X, CENTER_Y-175)))
        screen.blit(album_surf,     album_surf.get_rect(center=(CENTER_X, CENTER_Y-120)))
        screen.blit(title_surf,     title_surf.get_rect(center=(CENTER_X, CENTER_Y+120)))

        # Przyciski
        screen.blit(btn_prev_icon,         rect_prev)
        screen.blit(current_play_button(), rect_play)
        screen.blit(btn_next_icon,         rect_next)

        pygame.display.flip()
        clock.tick(30)

    return None