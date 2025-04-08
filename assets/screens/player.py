# player.py
import os
import sys
import math
import time
import pygame
import cairosvg
import io

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_player_screen(test_mode=False):
    pygame.init()

    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    # Tworzymy okno 800×800 w test_mode, w przeciwnym razie FULLSCREEN
    screen = (
        pygame.display.set_mode((WIDTH, HEIGHT))
        if test_mode
        else pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    )
    pygame.display.set_caption("HifiClockPlayer")
    clock = pygame.time.Clock()
    running = True

    # Kolory
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    SEMI_BLACK = (0, 0, 0, 128)  # np. 50% nakładka

    # Fonty
    font_regular = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_performer = pygame.font.Font(font_bold, 50)    # Wykonawca
    font_album     = pygame.font.Font(font_regular, 50) # Album
    font_title     = pygame.font.Font(font_regular, 50) # Tytuł

    # Przykładowe dane
    performer_text = "Pearl Jam"
    album_text     = "Dark Matter"
    title_text     = "Waiting for Stevie"

    def load_svg_button(filename):
        svg_path = os.path.join(BASE_DIR, "assets", "icons", filename)
        try:
            with open(svg_path, "rb") as svg_file:
                svg_data = svg_file.read()
            # Każdy przycisk 158×158
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=158, output_height=158)
            button_surf = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
            return button_surf
        except Exception as e:
            print("Nie udało się załadować przycisku:", filename, e)
            fallback = pygame.Surface((158, 158))
            fallback.fill((100, 0, 0))
            return fallback

    # Ładowanie przycisków
    btn_play  = load_svg_button("btn_play.svg")
    btn_pause = load_svg_button("btn_pause.svg")
    btn_prev  = load_svg_button("btn_prev.svg")
    btn_next  = load_svg_button("btn_next.svg")

    # Przełączanie play/pause
    is_playing = False
    def current_play_button():
        return btn_pause if is_playing else btn_play

    # Ładowanie okładki (cover.png 800×800)
    cover_path = os.path.join(BASE_DIR, "assets", "images", "cover.png")
    cover_img = None
    if os.path.exists(cover_path):
        try:
            cover_img = pygame.image.load(cover_path).convert()
            cover_img = pygame.transform.smoothscale(cover_img, (WIDTH, HEIGHT))
        except Exception as e:
            print("Nie udało się wczytać okładki:", e)

    # Parametry pierścienia
    RADIUS_OUTER = 380
    RING_WIDTH   = 16  # ~16 px
    RADIUS_INNER = RADIUS_OUTER - RING_WIDTH

    def draw_progress_ring(surface, progress):
        """
        Rysuje łuk postępu od godz.12, rosnący zgodnie z ruchem wskazówek,
        w pełnym kryciu, a potem ustawia alpha=128 (50%).
        """
        arc_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        color_full = (255, 255, 255, 255)  # biały, 100% krycia

        arc_rect = (
            CENTER_X - RADIUS_OUTER,
            CENTER_Y - RADIUS_OUTER,
            RADIUS_OUTER * 2,
            RADIUS_OUTER * 2
        )

        start_angle = -90
        end_angle = -90 - 360 * progress  # rosnący do dołu (CW)

        angle1 = min(start_angle, end_angle)
        angle2 = max(start_angle, end_angle)

        pygame.draw.arc(
            arc_surf,
            color_full,
            arc_rect,
            math.radians(angle1),
            math.radians(angle2),
            RING_WIDTH
        )

        arc_surf.set_alpha(128)  # 50% alpha
        surface.blit(arc_surf, (0, 0))

    # Testowy postęp
    track_progress = 0.3

    # Dla obsługi gestów
    start_y = None

    # Wersja docelowa: przesunięcie od dołu do góry w ~200 px (jeśli chcemy w pikselach),
    # ale jeśli w dotyku to e.y w [0..1], wtedy zrobimy np. 0.8 -> 0.55. Póki co zostawiamy px dla prostoty.
    SWIPE_THRESHOLD = 200

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if test_mode:
                # --- W trybie testowym obsługujemy SCROLL MYSZY ---
                if event.type == pygame.MOUSEWHEEL:
                    # scroll up => powrót do clock
                    if event.y > 0:
                        return "clock"
            else:
                # --- W trybie normalnym: Gest dotyku w pionie (finger) ---
                # Zamiast MOUSEBUTTONDOWN/UP => FINGERDOWN/UP
                if event.type == pygame.FINGERDOWN:
                    start_y = event.y * HEIGHT  # zmieniamy na piksele
                elif event.type == pygame.FINGERUP:
                    if start_y is not None:
                        end_y = event.y * HEIGHT
                        # Różnica ujemna => swipe w górę
                        delta_y = start_y - end_y
                        # start_y near bottom + move up > SWIPE_THRESHOLD
                        if start_y > (HEIGHT - 100) and delta_y > SWIPE_THRESHOLD:
                            return "clock"

            # Ewentualnie obsługa klikania w przyciski itp.
            if event.type == pygame.MOUSEBUTTONUP and test_mode:
                mx, my = event.pos
                # Sprawdź, czy kliknięto w obszar przycisków...
                # (zostawiamy w razie potrzeby)

        # Rysowanie tła
        screen.fill((0, 0, 0))

        # Okładka
        if cover_img:
            cover_surf = cover_img.copy()
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(SEMI_BLACK)
            cover_surf.blit(overlay, (0, 0))
            screen.blit(cover_surf, (0, 0))

        # Rysowanie pierścienia
        draw_progress_ring(screen, track_progress)

        # Teksty
        performer_surf = font_performer.render(performer_text, True, WHITE)
        album_surf     = font_album.render(album_text,      True, WHITE)
        title_surf     = font_title.render(title_text,      True, WHITE)

        performer_rect = performer_surf.get_rect(center=(CENTER_X, CENTER_Y - 240))
        album_rect     = album_surf.get_rect(center=(CENTER_X, CENTER_Y - 160))

        # Przyciski w oryginalnych pozycjach
        mid_y = CENTER_Y
        spacing = 200
        btn_prev_rect = btn_prev.get_rect(center=(CENTER_X - spacing, mid_y))
        btn_play_rect = current_play_button().get_rect(center=(CENTER_X, mid_y))
        btn_next_rect = btn_next.get_rect(center=(CENTER_X + spacing, mid_y))

        title_rect = title_surf.get_rect(center=(CENTER_X, mid_y + 160))

        # Rysowanie
        screen.blit(performer_surf, performer_rect)
        screen.blit(album_surf, album_rect)
        screen.blit(btn_prev, btn_prev_rect)
        screen.blit(current_play_button(), btn_play_rect)
        screen.blit(btn_next, btn_next_rect)
        screen.blit(title_surf, title_rect)

        pygame.display.flip()
        clock.tick(60 if test_mode else 30)

    pygame.quit()
    return None