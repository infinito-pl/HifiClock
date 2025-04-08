# clock.py

import os
import pygame
import time
import math
import requests
import io
import cairosvg
import locale
from datetime import datetime, time as dt_time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_clock_screen(screen, test_mode=False):
    """
    Wywoływana z main.py, otrzymuje gotowy obiekt 'screen'.

    - W nocy (21:00–5:00) nie rysujemy fal, a ikony tintujemy na czerwono.
    - W dzień rysujemy fale i używamy oryginalnych ikon białych.
    - Gdy user 'swipe' z góry na dół (RPi) lub scroll w dół (test_mode) => return "player".
    - Gdy user QUIT => return None.
    """

    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")

    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2
    RADIUS_OUTER = 380
    RADIUS_INNER = 370
    RADIUS_OUTER_LONG = 388
    RADIUS_INNER_LONG = 362

    clock = pygame.time.Clock()

    # Kolory dzienne
    DAY_WHITE = (255, 255, 255)
    DAY_DARK_GRAY = (51, 51, 51)

    # Kolory nocne (czerwonawy)
    NIGHT_WHITE = (200, 50, 50)
    NIGHT_DARK_GRAY = (30, 10, 10)

    # Na start – dzień
    WHITE = DAY_WHITE
    DARK_GRAY = DAY_DARK_GRAY

    font_regular = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_large = pygame.font.Font(font_bold, 212)
    font_small = pygame.font.Font(font_regular, 38)
    font_date  = pygame.font.Font(font_regular, 50)
    font_temp  = pygame.font.Font(font_bold, 38)

    # Pogodowa ikona domyślna
    weather_icon = pygame.Surface((62, 48))
    weather_icon.fill((255, 255, 255))
    icon_cache = {}

    # Klepsydra (00d.svg)
    hourglass_icon = None
    hourglass_angle = 0.0
    hourglass_flip_interval = 3.0
    hourglass_flip_duration = 0.3
    hourglass_rotating = False
    hourglass_rotate_start = 0.0
    hourglass_state = 0  # 0 => 0°, 1 => 180°
    last_hourglass_flip = time.time()

    def load_svg_icon(svg_filename, w=62, h=48):
        """
        Ładuje plik .svg do PNG (w,h) i zwraca go jako pygame.Surface
        """
        path = os.path.join(BASE_DIR, "assets", "icons", svg_filename)
        try:
            with open(path, "rb") as svg_file:
                svg_data = svg_file.read()
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=w, output_height=h)
            surf = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
            return surf
        except Exception as e:
            print(f"[Hourglass] Błąd ładowania {svg_filename}:", e)
            fallback = pygame.Surface((w, h))
            fallback.fill((200, 200, 200))
            return fallback

    # Ładujemy klepsydrę
    hourglass_icon = load_svg_icon("00d.svg", 62, 48)

    def colorize_icon(icon_surf, color):
        """
        Tworzy 'tintowaną' kopię danej ikony na wybrany kolor
        (wykorzystuje BLEND_RGBA_MULT – multiply).
        Sprawdza się, gdy oryginał jest w odcieniach bieli.
        """
        tinted = icon_surf.copy()
        tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
        return tinted

    def load_weather_icon(code):
        fallback_map = {
            "03d": "02d", "03n": "02n",
            "04n": "04d",
            "09n": "09d",
            "10n": "10d",
            "11n": "11d",
            "13n": "13d",
            "50n": "50d"
        }
        actual_code = fallback_map.get(code, code)
        svg_path = os.path.join(BASE_DIR, "assets", "icons", f"{actual_code}.svg")

        if actual_code not in icon_cache:
            try:
                with open(svg_path, "rb") as svg_file:
                    svg_data = svg_file.read()
                png_data = cairosvg.svg2png(bytestring=svg_data, output_width=62, output_height=48)
                icon_surf = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
                icon_cache[actual_code] = icon_surf
            except Exception as e:
                print("Błąd ładowania ikony pogody", actual_code, ":", e)
                fallback = pygame.Surface((62, 48))
                fallback.fill((255, 255, 255))
                icon_cache[actual_code] = fallback

        return icon_cache[actual_code]

    def get_city_from_ip():
        try:
            r = requests.get("https://ipinfo.io/json", timeout=5)
            return r.json().get("city", "")
        except:
            return ""

    def get_weather_data(city, api_key):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            r = requests.get(url, timeout=5)
            d = r.json()
            temp = round(d["main"]["temp"])
            desc = d["weather"][0]["description"].capitalize()
            icon_code = d["weather"][0]["icon"]
            w_icon = load_weather_icon(icon_code)
            return f"{temp}°C | {desc} in {city}", w_icon
        except:
            return None, None

    # Fale – dzienna/nocna
    day_colors = [
        (45, 105, 140),
        (80, 0, 160),
        (160, 40, 40),
        (160, 0, 160),
        (20, 20, 20),
    ]
    night_colors = [
        (90, 15, 15),
        (110, 0, 0),
        (40, 0, 40),
        (20, 10, 10),
        (10, 0, 0),
    ]

    def draw_wave_background(surface, time_offset, is_night):
        """
        Gdy is_night – brak fal, wypełniamy na czarno.
        """
        if is_night:
            surface.fill((0, 0, 0))
            return

        # W dzień – oryginalne fale
        surface.fill((0, 0, 0))
        colors = day_colors

        for i in range(5):
            wave_surf = pygame.Surface((WIDTH, HEIGHT * 2), pygame.SRCALPHA)
            freq = 0.005 + i * 0.002
            base_amp = 16 + (5 - i) * 3
            amp = base_amp + math.sin(time_offset * 2 + i) * 14
            speed = 0.03 + i * 0.01
            wcol = colors[i % len(colors)]

            for x in range(0, WIDTH, 2):
                phase = (x + time_offset * 100 * speed) * freq
                y = int(CENTER_Y + math.sin(phase) * amp)
                pygame.draw.line(wave_surf, wcol, (x, y), (x, HEIGHT))
            surface.blit(wave_surf, (0, 0))

    API_KEY = "3ca806c1d8f158812419bec229533068"
    city = get_city_from_ip()
    weather_text = "Loading weather..."
    weather_data_loaded = False

    last_weather_check = 0
    last_weather_try = 0

    prev_time_text = ""
    fade_progress = 1.0
    fade_start_time = 0
    fade_duration = 1.0
    prev_ring_surface = None
    current_ring_surface = None

    running = True
    start_y = None
    SWIPE_THRESHOLD = 0.25

    while running:
        now_dt = datetime.now()
        now_time = time.time()
        current_time_str = now_dt.strftime("%H:%M")
        current_second = now_dt.second
        current_date_str = now_dt.strftime("%a, %d %B %Y")
        current_hour_minute = now_dt.time()

        # Noc czy dzień
        is_night = not (dt_time(5, 0) <= current_hour_minute < dt_time(21, 0))

        # Ustawiamy kolory do rysowania fontów i kresek
        if is_night:
            WHITE = NIGHT_WHITE
            DARK_GRAY = NIGHT_DARK_GRAY
        else:
            WHITE = DAY_WHITE
            DARK_GRAY = DAY_DARK_GRAY

        # Jasność ekranu
        if not test_mode and (now_time - last_weather_check > 60):
            last_weather_check = now_time
            if is_night:
                os.system("echo 50 | sudo tee /sys/class/backlight/*/brightness > /dev/null")
            else:
                os.system("echo 192 | sudo tee /sys/class/backlight/*/brightness > /dev/null")

        # Tło fal (albo czarne w nocy)
        draw_wave_background(screen, now_time, is_night)

        # Fade przy zmianie minuty
        if current_time_str != prev_time_text:
            fade_progress = 0.0
            fade_start_time = now_time
            prev_time_text = current_time_str
            prev_ring_surface = current_ring_surface

        # Pogoda co 5s
        if (now_time - last_weather_try > 5) and (not weather_data_loaded or (now_time - last_weather_check > 900)):
            wtxt, wicon = get_weather_data(city, API_KEY)
            if wtxt:
                print("[DEBUG] Dane pogodowe załadowane pomyślnie")
                weather_text = wtxt
                weather_icon = wicon
                weather_data_loaded = True
                last_weather_check = now_time
            else:
                print("[DEBUG] Pogoda niedostępna, spróbuję ponownie...")
            last_weather_try = now_time

        # Rysowanie daty
        date_surf = font_date.render(current_date_str, True, WHITE)
        date_rect = date_surf.get_rect(center=(CENTER_X, CENTER_Y - 120))
        screen.blit(date_surf, date_rect)

        # Fade animacja czasu
        elapsed = now_time - fade_start_time
        if fade_progress < 1.0:
            fade_progress = min(1.0, elapsed / fade_duration)

        new_surf = font_large.render(current_time_str, True, WHITE)
        old_surf = font_large.render(prev_time_text, True, WHITE)
        new_surf.set_alpha(int(255 * fade_progress))
        old_surf.set_alpha(int(255 * (1.0 - fade_progress)))
        screen.blit(old_surf, old_surf.get_rect(center=(CENTER_X, CENTER_Y)))
        screen.blit(new_surf, new_surf.get_rect(center=(CENTER_X, CENTER_Y)))

        # Pogoda
        if not weather_data_loaded:
            weather_text = "Waiting for weather..."

        # Obcinamy ewentualną długość
        max_chars = 40
        if len(weather_text) > max_chars:
            weather_text = weather_text[: max_chars - 3] + "..."

        weather_surf = font_small.render(weather_text, True, WHITE)
        weather_rect = weather_surf.get_rect(center=(CENTER_X + 40, 547))
        screen.blit(weather_surf, weather_rect)

        icon_pos = (weather_rect.left - 70, weather_rect.centery - 24)

        # Ikona / klepsydra – w nocy colorizujemy
        if is_night:
            tinted_hourglass = colorize_icon(hourglass_icon, NIGHT_WHITE)
            tinted_weather   = colorize_icon(weather_icon,   NIGHT_WHITE)
        else:
            tinted_hourglass = hourglass_icon
            tinted_weather   = weather_icon

        if not weather_data_loaded:
            # Animacja klepsydry
            if not hourglass_rotating and (time.time() - last_hourglass_flip > hourglass_flip_interval):
                hourglass_rotating = True
                hourglass_rotate_start = now_time
                hourglass_state = 1 - hourglass_state

            if hourglass_rotating:
                t = (now_time - hourglass_rotate_start) / hourglass_flip_duration
                if t >= 1.0:
                    t = 1.0
                    hourglass_rotating = False
                    last_hourglass_flip = now_time
                base_angle = 0.0 if hourglass_state == 1 else 180.0
                target_angle = 180.0 if hourglass_state == 1 else 0.0
                hourglass_angle = base_angle + (target_angle - base_angle) * t
            else:
                hourglass_angle = 180.0 if hourglass_state == 1 else 0.0

            rotated_icon = pygame.transform.rotozoom(tinted_hourglass, hourglass_angle, 1.0)
            rotated_rect = rotated_icon.get_rect(center=(icon_pos[0] + 31, icon_pos[1] + 24))
            screen.blit(rotated_icon, rotated_rect)
        else:
            if is_night:
                # Pogodową też colorizujemy
                tinted_wicon = colorize_icon(weather_icon, NIGHT_WHITE)
                screen.blit(tinted_wicon, icon_pos)
            else:
                screen.blit(weather_icon, icon_pos)

        # Sekundowy ring
        current_ring_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(60):
            angle_deg = i * 6
            angle_rad = math.radians(angle_deg - 90)
            is_five = (i % 5 == 0)
            outer = RADIUS_OUTER_LONG if is_five else RADIUS_OUTER
            inner = RADIUS_INNER_LONG if is_five else RADIUS_INNER
            x1 = CENTER_X + outer * math.cos(angle_rad)
            y1 = CENTER_Y + outer * math.sin(angle_rad)
            x2 = CENTER_X + inner * math.cos(angle_rad)
            y2 = CENTER_Y + inner * math.sin(angle_rad)

            base_color = WHITE if i <= current_second else DARK_GRAY
            if fade_progress < 1.0:
                color = (*base_color[:3], int(255 * fade_progress))
            else:
                color = base_color

            pygame.draw.line(current_ring_surface, color, (x1, y1), (x2, y2), 2)

        if fade_progress < 1.0 and prev_ring_surface:
            prev_ring_surface.set_alpha(int(255 * (1.0 - fade_progress)))
            screen.blit(prev_ring_surface, (0, 0))
            current_ring_surface.set_alpha(int(255 * fade_progress))
            screen.blit(current_ring_surface, (0, 0))
        else:
            screen.blit(current_ring_surface, (0, 0))

        # Zdarzenia
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if test_mode:
                # scroll w dół => "player"
                if event.type == pygame.MOUSEWHEEL and event.y < 0:
                    return "player"
            else:
                # swipe z góry na dół
                if event.type == pygame.FINGERDOWN:
                    start_y = event.y
                elif event.type == pygame.FINGERUP and start_y is not None:
                    end_y = event.y
                    if start_y < 0.1 and (end_y - start_y) > SWIPE_THRESHOLD:
                        return "player"

        # FPS – 30 w dzień, 10 w nocy
        clock.tick(10 if is_night else 30)
        pygame.display.flip()

    return None