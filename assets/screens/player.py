# player.py

import os
import sys
import math
import time
import pygame
import cairosvg
import io

# Zakładamy, że plik metadata_shairport.py jest w katalogu services/
# i posiada funkcję get_current_track_info_shairport() → (title, artist, album, cover_path)
from services.metadata_shairport import get_current_track_info_shairport

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_player_screen(screen, test_mode=False):
    """
    Scena playera, korzystająca z layoutu:
    - Pierścień postępu z lewej (pionowo),
    - 3 przyciski duże (prev, play/pause, next) w centrum,
    - W górze: Artist, Album
    - W dole: Tytuł utworu
    - Domyślna okładka w tle (jeśli brak z metadanych)
    - Metadane z Shairport Sync (title, artist, album, cover_path)
    - Gest przejścia do "clock": w test_mode scroll up, w normalnym trybie swipe up
    """

    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    clock = pygame.time.Clock()
    running = True

    # Kolory
    WHITE = (255, 255, 255)
    BLACK = (0,   0,   0)
    SEMI_BLACK = (0,   0,   0, 128)  # 50% alpha

    # Fonty (zakładamy, że Barlow-Regular.ttf, Barlow-Bold.ttf są w assets/fonts)
    font_regular_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold_path    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")
    font_uppercase_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf").upper()

    font_artist  = pygame.font.Font(font_bold_path,    50)  # Wykonawca
    font_album   = pygame.font.Font(font_uppercase_path, 36)  # Album
    font_title   = pygame.font.Font(font_regular_path, 50)  # Tytuł utworu

    # Funkcja do ładowania .svg przycisków
    def load_svg_button(filename, width=158, height=158):
        full_path = os.path.join(BASE_DIR, "assets", "icons", filename)
        if not os.path.exists(full_path):
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255,0,0), (0,0,width,height), 5)
            return surf
        try:
            with open(full_path, "rb") as f:
                svg_data = f.read()
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=width, output_height=height)
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

    # Przyciski – docelowo (prev, play, next) w jednej linii horyzontalnie
    # Po środku ekranu w poziomie, w okolicach center_y
    # Przykładowo:
    btn_size = 158
    gap      = 40
    total_w  = btn_size * 3 + gap * 2
    start_x  = (WIDTH - total_w) // 2
    base_y   = (HEIGHT - btn_size) // 2

    rect_prev  = pygame.Rect(start_x,               base_y, btn_size, btn_size)
    rect_play  = pygame.Rect(start_x+btn_size+gap,  base_y, btn_size, btn_size)
    rect_next  = pygame.Rect(start_x+2*(btn_size+gap), base_y, btn_size, btn_size)

    # Domyślna okładka:
    default_cover_path = os.path.join(BASE_DIR, "assets", "images", "cover.png")

    # Sterujemy odtwarzaniem (do testów):
    is_playing = True

    def current_play_button():
        return btn_pause_icon if is_playing else btn_play_icon

    # Parametry "pierścienia" postępu:
    # W Twoim layoucie jest on po lewej, ~ od (0, ~200) do (0, ~600).
    # Załóżmy, że rysujemy łuk z wypełnieniem – szerokość 40 px
    # Start od godz.12, do np. 180 stopni w dół.
    # Ale z opisu i obrazka widać, że to "ćwiartka"? a może ~1/4 obwodu?

    # Poniżej wersja: ring na obwodzie koła 800 / 2 = 400 px,
    # a w rzeczywistości go przesuwasz w bok (może x=50?)
    # Dla uproszczenia – narysujemy go w pętli (like arc), z alpha
    RING_WIDTH = 25
    RING_RADIUS = 380

    # Do obsługi przesunięcia
    start_y = None
    SWIPE_THRESHOLD = 0.25  # (ułamek okna w trybie finger)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if test_mode:
                # scroll w górę => "clock"
                if event.type == pygame.MOUSEWHEEL and event.y > 0:
                    pygame.event.clear()
                    return "clock"
            else:
                # obsługa FINGER
                if event.type == pygame.FINGERDOWN:
                    start_y = event.y
                elif event.type == pygame.FINGERUP and start_y is not None:
                    if (start_y - event.y) > SWIPE_THRESHOLD:
                        pygame.event.clear()
                        return "clock"

            if event.type == pygame.MOUSEBUTTONUP:
                # Obsługa klikania
                mx, my = event.pos
                if rect_prev.collidepoint(mx,my):
                    print("[player] Prev pressed!")
                elif rect_play.collidepoint(mx,my):
                    print("[player] Play/Pause pressed!")
                    is_playing = not is_playing
                elif rect_next.collidepoint(mx,my):
                    print("[player] Next pressed!")

        # Tło
        screen.fill(BLACK)

        # Metadane z Shairport
        title, artist, album, cover_path = get_current_track_info_shairport()
        if not artist:
            artist = "Unknown artist"
        if not album:
            album = "Unknown album"
        if not title:
            title = "Unknown track"
        if not cover_path or not os.path.exists(cover_path):
            cover_path = default_cover_path

        # Rysujemy okładkę 800x800 z 50% opacity:
        try:
            cover_img = pygame.image.load(cover_path).convert()
            cover_img = pygame.transform.scale(cover_img, (WIDTH, HEIGHT))
            alpha_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha_surf.blit(cover_img, (0,0))
            alpha_surf.set_alpha(128)  # 50%
            screen.blit(alpha_surf, (0,0))
        except:
            pass

        # Rysujemy "pierścień" postępu – w oryginalnym stylu to widać
        # Poniżej wersja "solid arc" – zaczynamy od godz.12, np. 25% postęp
        progress = 0.25
        ring_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        color_ring = (255,255,255,180)  # lekko przezroczysty

        # Rysunek łuku
        # Start w (center_x, center_y), ale przesunięty w lewo? 
        # Na screenie jest "ćwiartka" – ciężko stwierdzić. 
        # W oryginalnym rysowałeś 60 kresek. 
        # Tu np. zamieniamy to na arc:
        rect_arc = (CENTER_X-RING_RADIUS, CENTER_Y-RING_RADIUS, 2*RING_RADIUS, 2*RING_RADIUS)
        start_angle = -90
        end_angle   = start_angle + 360*progress  # rosnący cw

        # Gdy chcesz, by to była "ćwiartka" z boku ekranu – musiałbyś klipować / zmienić offset
        pygame.draw.arc(ring_surf, color_ring, rect_arc,
                        math.radians(start_angle), math.radians(end_angle), RING_WIDTH)

        screen.blit(ring_surf, (0,0))

        # Teksty: performer (u góry?), album poniżej, a tytuł jeszcze niżej
        # W oryginalnym "Pearl Jam" ~y=130, "Dark Matter" ~y=190, "Waiting for Stevie" ~y=610?

        # Dla uproszczenia:
        performer_surf = font_artist.render(artist, True, WHITE)
        album_surf     = font_album.render(album,   True, WHITE)
        title_surf     = font_title.render(title,   True, WHITE)

        # Wg ekranu:
   
        # Mamy 800 pix, to dajmy:
        performer_rect = performer_surf.get_rect(center=(CENTER_X, CENTER_Y-175))
        album_rect     = album_surf.get_rect(center=(CENTER_X, CENTER_Y-125))
        title_rect     = title_surf.get_rect(center=(CENTER_X, CENTER_Y+125))

        screen.blit(performer_surf, performer_rect)
        screen.blit(album_surf,     album_rect)
        screen.blit(title_surf,     title_rect)

        # Trzy przyciski na ~center: 
        # oryginał: [prev, play, next] w ~ (center_x, 400)? 
        screen.blit(load_svg_button("btn_prev.svg"),  rect_prev)
        screen.blit(current_play_button(),            rect_play)
        screen.blit(load_svg_button("btn_next.svg"),  rect_next)

        pygame.display.flip()
        clock.tick(30)

    return None