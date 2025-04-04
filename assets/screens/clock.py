import os
import pygame
import time
import math
import requests
import io
import cairosvg
import locale
from datetime import datetime
from datetime import time as dt_time

# Bazowy katalog projektu
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

    DARK_RED = (160, 30, 30)
    NIGHT_BRIGHTNESS = 50
    DAY_BRIGHTNESS = 192

    screen = (
        pygame.display.set_mode((WIDTH, HEIGHT))
        if test_mode
        else pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    )
    pygame.display.set_caption("HiFiBox Clock")
    clock = pygame.time.Clock()

    WHITE = (255, 255, 255)
    DARK_GRAY = (51, 51, 51)

    font_regular = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_large = pygame.font.Font(font_bold, 212)
    font_small = pygame.font.Font(font_regular, 38)
    font_date = pygame.font.Font(font_regular, 50)
    font_temp = pygame.font.Font(font_bold, 38)

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
                    if is_night_time:
                        for x in range(icon_surface.get_width()):
                            for y in range(icon_surface.get_height()):
                                r, g, b, a = icon_surface.get_at((x, y))
                                if a > 0:
                                    icon_surface.set_at((x, y), (*DARK_RED, a))
                    icon_cache[actual_code] = icon_surface
            except Exception as e:
                print(f"Błąd ładowania ikony pogody {actual_code}: {e}")
                fallback = pygame.Surface((62, 48))
                fallback.fill(WHITE)
                icon_cache[actual_code] = fallback

        return icon_cache[actual_code]

    def get_city_from_ip():
        try:
            response = requests.get("https://ipinfo.io/json")
            data = response.json()
            return data.get("city", "")
        except:
            return ""

    def get_weather_data(city, api_key):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            temp = round(data['main']['temp'])
            description = data['weather'][0]['description'].capitalize()
            icon_code = data['weather'][0]['icon']
            weather_icon = load_weather_icon(icon_code)
            return f"{temp}°C | {description} in {city}", weather_icon
        except:
            return "--°C | Weather unavailable", pygame.Surface((62, 48))

    def draw_wave_background(surface, time_offset, is_night_time=False):
        surface.fill((0, 0, 0))
        night_colors = [
            (20, 20, 20),
            (25, 0, 30),
            (30, 0, 0),
            (35, 0, 10),
            (15, 0, 0)
        ]
        colors = night_colors if is_night_time else [
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
    while running:
        current_hour_minute = datetime.now().time()
        is_night_time = not (dt_time(5, 0) <= current_hour_minute < dt_time(21, 0))
        
        if time.time() - last_weather_check > 60:
            brightness = NIGHT_BRIGHTNESS if is_night_time else DAY_BRIGHTNESS
            os.system(f"echo {brightness} | sudo tee /sys/class/backlight/*/brightness > /dev/null")

        if fade_progress >= 1.0:
            prev_second = datetime.now().second

        draw_wave_background(screen, time.time(), is_night_time)

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%a, %d %B %Y")
        current_second = now.second

        active_color = DARK_RED if is_night_time else WHITE

        if current_time != prev_time_text:
            fade_progress = 0.0
            fade_start_time = time.time()
            prev_time_text = current_time
            prev_ring_surface = current_ring_surface

        # Próba pobrania danych pogodowych co 5 sekund jeśli nie zostały jeszcze załadowane lub co 15 minut po ich załadowaniu
        if (not weather_data_loaded or time.time() - last_weather_check > 900) and (time.time() - last_weather_try > 5):
            try:
                weather_text, weather_icon = get_weather_data(city, API_KEY)
                weather_data_loaded = True
                last_weather_check = time.time()
            except Exception as e:
                print("Pogoda niedostępna, spróbuję ponownie...", e)
            last_weather_try = time.time()

        if not weather_data_loaded:
            weather_text = "Waiting for weather..."

        date_surface = font_date.render(current_date, True, active_color)
        date_rect = date_surface.get_rect(center=(CENTER_X, CENTER_Y - 120))
        screen.blit(date_surface, date_rect)

        elapsed = time.time() - fade_start_time
        if fade_progress < 1.0:
            fade_progress = min(1.0, elapsed / fade_duration)

        new_surface = font_large.render(current_time, True, active_color)
        old_surface = font_large.render(prev_time_text, True, active_color)
        new_surface.set_alpha(int(255 * fade_progress))
        old_surface.set_alpha(int(255 * (1.0 - fade_progress)))
        screen.blit(old_surface, old_surface.get_rect(center=(CENTER_X, CENTER_Y)))
        screen.blit(new_surface, new_surface.get_rect(center=(CENTER_X, CENTER_Y)))

        max_chars = 40
        if len(weather_text) > max_chars:
            weather_text = weather_text[:max_chars - 3] + "..."
        weather_surface = font_small.render(weather_text, True, active_color)
        weather_rect = weather_surface.get_rect(center=(CENTER_X + 40, 547))
        screen.blit(weather_surface, weather_rect)
        icon_pos = (weather_rect.left - 70, weather_rect.centery - 24)
        screen.blit(weather_icon, icon_pos)

        inactive_color = (40, 0, 0) if is_night_time else DARK_GRAY
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
            base_color = active_color if i <= current_second else inactive_color
            color = (*base_color[:3], int(255 * fade_progress)) if fade_progress < 1.0 else base_color
            pygame.draw.line(current_ring_surface, color, (x1, y1), (x2, y2), 2)

        if fade_progress < 1.0 and prev_ring_surface:
            prev_ring_surface.set_alpha(int(255 * (1.0 - fade_progress)))
            screen.blit(prev_ring_surface, (0, 0))
            current_ring_surface.set_alpha(int(255 * fade_progress))
            screen.blit(current_ring_surface, (0, 0))
        else:
            screen.blit(current_ring_surface, (0, 0))

        clock.tick(30 if dt_time(5, 0) <= current_hour_minute < dt_time(21, 0) else 10)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    os.system("echo 50 | sudo tee /sys/class/backlight/*/brightness > /dev/null")
    pygame.quit()