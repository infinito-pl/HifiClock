import os
import pygame
import time
import math
import requests
import io
import cairosvg
import locale
from datetime import datetime, time as dt_time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def run_clock_screen(test_mode=False):
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    pygame.init()

    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2
    RADIUS_OUTER = 380
    RADIUS_INNER = 370
    RADIUS_OUTER_LONG = 388
    RADIUS_INNER_LONG = 362

    # Tworzymy okno w trybie test lub fullscreen
    screen = (
        pygame.display.set_mode((WIDTH, HEIGHT))
        if test_mode
        else pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    )
    pygame.display.set_caption("HiFiBox Clock")

    # Inicjalizujemy clock do sterowania FPS
    clock = pygame.time.Clock()

    # Kolory
    WHITE = (255, 255, 255)
    DARK_GRAY = (51, 51, 51)

    # Ścieżki do fontów
    font_regular = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_large  = pygame.font.Font(font_bold,    212)
    font_small  = pygame.font.Font(font_regular, 38)
    font_date   = pygame.font.Font(font_regular, 50)
    font_temp   = pygame.font.Font(font_bold,    38)

    # Ikona pogody tymczasowa (na starcie)
    weather_icon = pygame.Surface((62, 48))
    weather_icon.fill(WHITE)
    icon_cache = {}

    def load_weather_icon(code):
        fallback_map = {
            '03d': '02d', '03n': '02n',
            '04n': '04d',
            '09n': '09d',
            '10n': '10d',
            '11n': '11d',
            '13n': '13d',
            '50n': '50d'
        }
        actual_code = fallback_map.get(code, code)
        svg_path = os.path.join(BASE_DIR, "assets", "icons", f"{actual_code}.svg")

        if actual_code not in icon_cache:
            try:
                with open(svg_path, 'rb') as svg_file:
                    svg_data = svg_file.read()
                    png_data = cairosvg.svg2png(bytestring=svg_data, output_width=62, output_height=48)
                    icon_surface = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
                    icon_cache[actual_code] = icon_surface
            except Exception as e:
                print(f"Błąd ładowania ikony pogody {actual_code}: {e}")
                fallback = pygame.Surface((62, 48))
                fallback.fill(WHITE)
                icon_cache[actual_code] = fallback

        return icon_cache[actual_code]

    def get_city_from_ip():
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            return data.get("city", "")
        except:
            return ""

    def get_weather_data(city, api_key):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            temp = round(data['main']['temp'])
            description = data['weather'][0]['description'].capitalize()
            icon_code = data['weather'][0]['icon']
            w_icon = load_weather_icon(icon_code)
            return f"{temp}°C | {description} in {city}", w_icon
        except:
            return None, None

    def draw_wave_background(surface, time_offset):
        surface.fill((0, 0, 0))
        colors = [
            (45, 105, 140),
            (80, 0, 160),
            (160, 40, 40),
            (160, 0, 160),
            (20, 20, 20)
        ]
        for i in range(5):
            wave_surface = pygame.Surface((WIDTH, HEIGHT * 2), pygame.SRCALPHA)
            freq = 0.005 + i * 0.002
            base_amp = 16 + (5 - i) * 3
            amp = base_amp + math.sin(time_offset * 2 + i) * 14
            speed = 0.03 + i * 0.01
            wave_color = colors[i % len(colors)]
            for x in range(0, WIDTH, 2):
                phase = (x + time_offset * 100 * speed) * freq
                y = int(CENTER_Y + math.sin(phase) * amp)
                pygame.draw.line(wave_surface, wave_color, (x, y), (x, HEIGHT))
            surface.blit(wave_surface, (0, 0))

    API_KEY = "3ca806c1d8f158812419bec229533068"
    last_weather_check = 0
    weather_text = "Loading weather..."
    city = get_city_from_ip()

    weather_data_loaded = False
    last_weather_try = 0

    prev_time_text = ""
    fade_progress = 1.0
    fade_start_time = 0
    fade_duration = 1.0
    prev_second = -1
    prev_ring_surface = None
    current_ring_surface = None

    running = True
    start_y = None  # do gesta w pionie
    SWIPE_THRESHOLD = 200

    while running:
        current_hour_minute = datetime.now().time()

        # Jasność ekranu (pomijana, jeśli test_mode - by nie wymagać sudo)
        if not test_mode:
            if time.time() - last_weather_check > 60:
                if dt_time(5, 0) <= current_hour_minute < dt_time(21, 0):
                    os.system("echo 192 | sudo tee /sys/class/backlight/*/brightness > /dev/null")
                else:
                    os.system("echo 50 | sudo tee /sys/class/backlight/*/brightness > /dev/null")

        # Tło animowane
        draw_wave_background(screen, time.time())

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%a, %d %B %Y")
        current_second = now.second

        # Fade logika zmiany czasu
        if current_time != prev_time_text:
            fade_progress = 0.0
            fade_start_time = time.time()
            prev_time_text = current_time
            prev_ring_surface = current_ring_surface

        # Pobieranie pogody co 5s aż do skutku, a potem co 15 min
        if (time.time() - last_weather_try > 5) and (not weather_data_loaded or time.time() - last_weather_check > 900):
            w_text_candidate, w_icon_candidate = get_weather_data(city, API_KEY)
            if w_text_candidate:
                print("[DEBUG] Dane pogodowe załadowane pomyślnie")
                weather_text = w_text_candidate
                weather_icon = w_icon_candidate
                weather_data_loaded = True
                last_weather_check = time.time()
            else:
                print("[DEBUG] Pogoda niedostępna, spróbuję ponownie...")
            last_weather_try = time.time()

        # Rysowanie daty
        date_surface = font_date.render(current_date, True, WHITE)
        date_rect = date_surface.get_rect(center=(CENTER_X, CENTER_Y - 120))
        screen.blit(date_surface, date_rect)

        # Fade logika
        elapsed = time.time() - fade_start_time
        if fade_progress < 1.0:
            fade_progress = min(1.0, elapsed / fade_duration)

        new_surface = font_large.render(current_time, True, WHITE)
        old_surface = font_large.render(prev_time_text, True, WHITE)
        new_surface.set_alpha(int(255 * fade_progress))
        old_surface.set_alpha(int(255 * (1.0 - fade_progress)))
        screen.blit(old_surface, old_surface.get_rect(center=(CENTER_X, CENTER_Y)))
        screen.blit(new_surface, new_surface.get_rect(center=(CENTER_X, CENTER_Y)))

        # Pogoda
        if not weather_data_loaded:
            weather_text = "Waiting for weather..."
        max_chars = 40
        if len(weather_text) > max_chars:
            weather_text = weather_text[:max_chars - 3] + "..."
        weather_surface = font_small.render(weather_text, True, WHITE)
        weather_rect = weather_surface.get_rect(center=(CENTER_X + 40, 547))
        screen.blit(weather_surface, weather_rect)
        icon_pos = (weather_rect.left - 70, weather_rect.centery - 24)

        # Ikona pogody (klepsydra obracana, jeśli czekamy - tu pominęliśmy, bo jest w poprzednich wersjach)
        screen.blit(weather_icon, icon_pos)

        # Rysowanie pierścienia sekund
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
            color = (*base_color[:3], int(255 * fade_progress)) if fade_progress < 1.0 else base_color
            pygame.draw.line(current_ring_surface, color, (x1, y1), (x2, y2), 2)

        if fade_progress < 1.0 and prev_ring_surface:
            prev_ring_surface.set_alpha(int(255 * (1.0 - fade_progress)))
            screen.blit(prev_ring_surface, (0, 0))
            current_ring_surface.set_alpha(int(255 * fade_progress))
            screen.blit(current_ring_surface, (0, 0))
        else:
            screen.blit(current_ring_surface, (0, 0))

        # Obsługa zdarzeń
        for event in pygame.event.get():
            print(event) #Pokaż zdarzenia
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                start_y = event.pos[1]

            elif event.type == pygame.MOUSEBUTTONUP:
                if start_y is not None:
                    end_y = event.pos[1]
                    delta_y = end_y - start_y

                    # Gest z góry na dół
                    if start_y < 100 and delta_y > SWIPE_THRESHOLD:
                        # Przechodzimy do playera
                        return "player"

                # Tryb test: klik w dolnej części
                if test_mode:
                    mx, my = event.pos
                    if my > 700:
                        return "player"

        # Odświeżanie klatek
        clock.tick(30 if dt_time(5, 0) <= current_hour_minute < dt_time(21, 0) else 10)
        pygame.display.flip()

    # Jeśli user wyszedł, brak przejścia do playera
    return None