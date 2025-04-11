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
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, WEATHER_API_KEY, WEATHER_UPDATE_INTERVAL, WEATHER_ICON_SIZE
from ui.screens.base import BaseScreen
from utils.logging import logger
from services.weather.weather import get_weather_data

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class ClockScreen(BaseScreen):
    def __init__(self, screen):
        super().__init__(screen)
        self.font_time = pygame.font.Font(FONTS['BOLD'], 100)
        self.font_date = pygame.font.Font(FONTS['REGULAR'], 30)
        self.font_temp = pygame.font.Font(FONTS['REGULAR'], 50)
        
        # Inicjalizacja danych pogodowych
        self.weather_data = None
        self.last_weather_update = 0
        self.weather_update_interval = 1800  # 30 minut
        
        # Załaduj ikonę pogody
        self.weather_icon = None
        self.weather_icon_path = None
        self.load_weather_icon()

    def load_weather_icon(self):
        """Ładuje ikonę pogody."""
        try:
            weather_icon_path = "assets/images/weather/clear.png"  # Domyślna ikona
            if self.weather_data and 'icon' in self.weather_data:
                weather_icon_path = f"assets/images/weather/{self.weather_data['icon']}.png"
            self.weather_icon = pygame.image.load(weather_icon_path)
            self.weather_icon = pygame.transform.scale(self.weather_icon, WEATHER_ICON_SIZE)
            self.weather_icon_path = weather_icon_path
            logger.debug(f"Loaded weather icon: {weather_icon_path}")
        except Exception as e:
            logger.error(f"Błąd ładowania ikony pogody: {e}")
            self.weather_icon = None
            self.weather_icon_path = None

    def update_weather(self):
        """Aktualizuje dane pogodowe."""
        current_time = time.time()
        if current_time - self.last_weather_update > self.weather_update_interval:
            try:
                # Najpierw pobierz lokalizację
                location_response = requests.get('http://ip-api.com/json/')
                location_data = location_response.json()
                city = location_data.get('city', 'Wroclaw')  # Domyślnie Wrocław

                # Następnie pobierz pogodę
                weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
                response = requests.get(weather_url)
                self.weather_data = response.json()
                
                # Załaduj odpowiednią ikonę
                icon_code = self.weather_data['weather'][0]['icon']
                self.load_weather_icon()
                
                self.last_weather_update = current_time
                logger.debug(f"Weather updated for {city}")
            except Exception as e:
                logger.error(f"Błąd aktualizacji pogody: {e}")

    def update(self):
        """Aktualizuje stan ekranu."""
        self.update_weather()

    def draw(self):
        """Rysuje ekran zegara."""
        super().draw()
        
        # Pobierz aktualny czas
        current_time = time.strftime("%H:%M")
        current_date = time.strftime("%A, %d %B %Y")
        
        # Rysuj czas
        time_text = self.font_time.render(current_time, True, COLORS['WHITE'])
        time_rect = time_text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(time_text, time_rect)
        
        # Rysuj datę
        date_text = self.font_date.render(current_date, True, COLORS['WHITE'])
        date_rect = date_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
        self.screen.blit(date_text, date_rect)
        
        # Rysuj temperaturę i ikonę pogody
        if self.weather_data and self.weather_icon:
            temp_text = self.font_temp.render(f"{self.weather_data['temp']}°C", True, COLORS['WHITE'])
            temp_rect = temp_text.get_rect(center=(self.width // 2, self.height // 2 + 100))
            self.screen.blit(temp_text, temp_rect)
            
            icon_rect = self.weather_icon.get_rect(center=(self.width // 2, self.height // 2 + 170))
            self.screen.blit(self.weather_icon, icon_rect)

    def run(self):
        """Uruchamia ekran zegara."""
        result = super().run()
        if result == "swipe_down":
            return "player"
        return result

def run_clock_screen(screen):
    """
    Funkcja uruchamiana z main.py, otrzymuje obiekt 'screen' już utworzony.
    Nie kończy programu, lecz w razie potrzeby zwraca "player" (do przejścia),
    albo None, jeśli użytkownik zamknie okno (QUIT) lub pętla się zakończy.
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

    # Kolory w trybie dziennym
    DAY_WHITE = (255, 255, 255)
    DAY_DARK_GRAY = (51, 51, 51)

    # Kolory w trybie nocnym (czerwonawe)
    NIGHT_WHITE = (200, 50, 50)
    NIGHT_DARK_GRAY = (30, 10, 10)

    # Na start zakładamy kolory dzienne (i tak nadpiszemy je w pętli)
    WHITE = DAY_WHITE
    DARK_GRAY = DAY_DARK_GRAY

    # Fonty
    font_regular = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold    = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_large = pygame.font.Font(font_bold, 212)
    font_small = pygame.font.Font(font_regular, 38)
    font_date  = pygame.font.Font(font_regular, 50)
    font_temp  = pygame.font.Font(font_bold, 38)

    # Ikona pogodowa tymczasowa
    weather_icon = pygame.Surface((62, 48))
    weather_icon.fill((255, 255, 255))
    icon_cache = {}

    # Klepsydra (00d.svg) do animowania przy braku danych pogodowych
    hourglass_icon = None
    hourglass_angle = 0.0
    hourglass_flip_interval = 3.0
    hourglass_flip_duration = 0.3
    hourglass_rotating = False
    hourglass_rotate_start = 0.0
    hourglass_state = 0     # 0 => 0°, 1 => 180°
    last_hourglass_flip = time.time()

    def load_svg_icon(svg_filename, w=62, h=48):
        """
        Ładuje plik .svg i zwraca go jako pygame.Surface
        """
        path = os.path.join(BASE_DIR, "assets", "icons", svg_filename)
        try:
            with open(path, "rb") as svg_file:
                svg_data = svg_file.read()
            png_data = cairosvg.svg2png(
                bytestring=svg_data,
                output_width=w,
                output_height=h
            )
            surf = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
            return surf
        except Exception as e:
            print("[Hourglass] Błąd ładowania", svg_filename, ":", e)
            fallback = pygame.Surface((w, h))
            fallback.fill((200, 200, 200))
            return fallback

    # Ładujemy plik 00d.svg (klepsydra)
    hourglass_icon = load_svg_icon("00d.svg", 62, 48)

    # Obsługa ikon pogodowych (cache)
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
        
        # Jeśli mamy ikonę w cache, zwróć ją
        if code in icon_cache:
            return icon_cache[code]
            
        # Jeśli nie mamy ikony, spróbuj załadować
        try:
            # Najpierw spróbuj załadować oryginalną ikonę
            icon = load_svg_icon(f"{code}.svg")
            icon_cache[code] = icon
            return icon
        except Exception as e:
            # Jeśli nie udało się załadować, spróbuj użyć fallback
            fallback_code = fallback_map.get(code, "00d")
            try:
                icon = load_svg_icon(f"{fallback_code}.svg")
                icon_cache[code] = icon
                return icon
            except Exception as e:
                # Jeśli i to się nie udało, zwróć klepsydrę
                return hourglass_icon

    # Inicjalizacja danych pogodowych
    weather_data = None
    last_weather_update = 0
    weather_update_interval = 1800  # 30 minut

    # Inicjalizacja danych o czasie
    last_time = time.time()
    last_weather_check = time.time()
    last_hourglass_flip = time.time()

    # Główna pętla
    running = True
    while running:
        # Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.FINGERDOWN:
                start_y = event.y * HEIGHT
            elif event.type == pygame.FINGERUP:
                end_y = event.y * HEIGHT
                delta_y = start_y - end_y
                if delta_y > 0.25:  # Przesunięcie w dół
                    return "player"

        # Aktualizacja czasu
        now_time = time.time()
        if now_time - last_time >= 1.0:  # Co sekundę
            last_time = now_time
            current_time = time.localtime()
            current_hour = current_time.tm_hour

            # Aktualizacja kolorów w zależności od pory dnia
            if 6 <= current_hour < 18:  # Dzień
                WHITE = DAY_WHITE
                DARK_GRAY = DAY_DARK_GRAY
            else:  # Noc
                WHITE = NIGHT_WHITE
                DARK_GRAY = NIGHT_DARK_GRAY

            # Aktualizacja pogody
            if now_time - last_weather_update >= weather_update_interval:
                try:
                    weather_data = get_weather_data()
                    last_weather_update = now_time
                except Exception as e:
                    logger.error(f"Błąd aktualizacji pogody: {e}")

            # Jasność ekranu (co 60s)
            if now_time - last_weather_check > 60:
                last_weather_check = now_time
                # Tutaj można dodać kod do zmiany jasności ekranu

        # Rysowanie
        screen.fill(DARK_GRAY)

        # Rysowanie zegara
        current_time = time.localtime()
        hour = current_time.tm_hour % 12
        minute = current_time.tm_min
        second = current_time.tm_sec

        # Rysowanie tarczy
        pygame.draw.circle(screen, WHITE, (CENTER_X, CENTER_Y), RADIUS_OUTER)
        pygame.draw.circle(screen, DARK_GRAY, (CENTER_X, CENTER_Y), RADIUS_INNER)

        # Rysowanie wskazówek
        hour_angle = math.radians((hour * 30) + (minute * 0.5) - 90)
        minute_angle = math.radians((minute * 6) + (second * 0.1) - 90)
        second_angle = math.radians((second * 6) - 90)

        # Godzina
        hour_x = CENTER_X + (RADIUS_INNER * 0.6) * math.cos(hour_angle)
        hour_y = CENTER_Y + (RADIUS_INNER * 0.6) * math.sin(hour_angle)
        pygame.draw.line(screen, WHITE, (CENTER_X, CENTER_Y), (hour_x, hour_y), 8)

        # Minuty
        minute_x = CENTER_X + (RADIUS_INNER * 0.8) * math.cos(minute_angle)
        minute_y = CENTER_Y + (RADIUS_INNER * 0.8) * math.sin(minute_angle)
        pygame.draw.line(screen, WHITE, (CENTER_X, CENTER_Y), (minute_x, minute_y), 4)

        # Sekundy
        second_x = CENTER_X + (RADIUS_INNER * 0.9) * math.cos(second_angle)
        second_y = CENTER_Y + (RADIUS_INNER * 0.9) * math.sin(second_angle)
        pygame.draw.line(screen, WHITE, (CENTER_X, CENTER_Y), (second_x, second_y), 2)

        # Rysowanie cyfr
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            x = CENTER_X + (RADIUS_OUTER * 0.85) * math.cos(angle)
            y = CENTER_Y + (RADIUS_OUTER * 0.85) * math.sin(angle)
            number = str(i if i != 0 else 12)
            text = font_small.render(number, True, WHITE)
            text_rect = text.get_rect(center=(x, y))
            screen.blit(text, text_rect)

        # Rysowanie daty
        date_text = time.strftime("%A, %d %B %Y")
        date_surface = font_date.render(date_text, True, WHITE)
        date_rect = date_surface.get_rect(center=(CENTER_X, CENTER_Y + RADIUS_OUTER + 50))
        screen.blit(date_surface, date_rect)

        # Rysowanie temperatury i ikony pogody
        if weather_data:
            temp_text = f"{weather_data['temp']}°C"
            temp_surface = font_temp.render(temp_text, True, WHITE)
            temp_rect = temp_surface.get_rect(center=(CENTER_X, CENTER_Y + RADIUS_OUTER + 100))
            screen.blit(temp_surface, temp_rect)

            weather_icon = load_weather_icon(weather_data['icon'])
            icon_rect = weather_icon.get_rect(center=(CENTER_X, CENTER_Y + RADIUS_OUTER + 150))
            screen.blit(weather_icon, icon_rect)
        else:
            # Animacja klepsydry
            if now_time - last_hourglass_flip >= hourglass_flip_interval:
                hourglass_rotating = True
                hourglass_rotate_start = now_time
                last_hourglass_flip = now_time
                hourglass_state = 1 - hourglass_state  # Przełącz stan

            if hourglass_rotating:
                elapsed = now_time - hourglass_rotate_start
                if elapsed < hourglass_flip_duration:
                    progress = elapsed / hourglass_flip_duration
                    hourglass_angle = 180 * progress if hourglass_state == 1 else 180 * (1 - progress)
                else:
                    hourglass_rotating = False
                    hourglass_angle = 180 if hourglass_state == 1 else 0

            rotated_icon = pygame.transform.rotate(hourglass_icon, hourglass_angle)
            icon_rect = rotated_icon.get_rect(center=(CENTER_X, CENTER_Y + RADIUS_OUTER + 150))
            screen.blit(rotated_icon, icon_rect)

        pygame.display.flip()
        clock.tick(60)