# clock.py

import os
import sys
import math
import time
import pygame
import cairosvg
import io
import locale
import logging
from datetime import datetime
from config import COLORS, FONTS, ICONS_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, WEATHER_API_KEY, WEATHER_UPDATE_INTERVAL, WEATHER_ICON_SIZE
from ui.screens.base import BaseScreen
from services.weather.weather import get_weather_data
from utils.logging import logger

class ClockScreen(BaseScreen):
    def __init__(self, screen):
        super().__init__(screen)
        
        # Fonty
        self.font_large = pygame.font.Font(FONTS["BOLD"], 212)
        self.font_small = pygame.font.Font(FONTS["REGULAR"], 38)
        self.font_date = pygame.font.Font(FONTS["REGULAR"], 50)
        self.font_temp = pygame.font.Font(FONTS["BOLD"], 38)

        # Ikona pogodowa tymczasowa
        self.weather_icon = None
        self.icon_cache = {}
        
        # Klepsydra (00d.svg) do animowania przy braku danych pogodowych
        self.hourglass_icon = None
        self.hourglass_angle = 0.0
        self.hourglass_flip_interval = 3.0
        self.hourglass_flip_duration = 0.3
        self.hourglass_rotating = False
        self.hourglass_rotate_start = 0.0
        self.hourglass_state = 0     # 0 => 0°, 1 => 180°
        self.last_hourglass_flip = time.time()
        
        # Ładujemy plik 00d.svg (klepsydra)
        self.hourglass_icon = self.load_svg_icon("00d.svg", 62, 48)
        
        # Inicjalizacja danych pogodowych
        self.weather_data = None
        self.last_weather_update = 0
        self.weather_update_interval = 1800  # 30 minut
        
        # Ustawienie lokalizacji dla formatowania daty
        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")

    def load_svg_icon(self, svg_filename, w=62, h=48):
        """Ładuje plik .svg i zwraca go jako pygame.Surface"""
        path = os.path.join(ICONS_DIR, svg_filename)
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
            logger.error(f"Błąd ładowania ikony {svg_filename}: {e}")
            fallback = pygame.Surface((w, h))
            fallback.fill((200, 200, 200))
            return fallback

    def load_weather_icon(self, code):
        """Ładuje ikonę pogodową z cache lub z pliku"""
        fallback_map = {
            "03d": "02d", "03n": "02n",
            "04n": "04d",
            "09n": "09d",
            "10n": "10d",
            "11n": "11d",
            "13n": "13d",
            "50n": "50d"
        }
        
        # Użyj mapowania fallback jeśli jest dostępne
        actual_code = fallback_map.get(code, code)
        
        # Jeśli mamy ikonę w cache, zwróć ją
        if actual_code in self.icon_cache:
            return self.icon_cache[actual_code]
            
        # Jeśli nie mamy ikony, spróbuj załadować
        try:
            icon = self.load_svg_icon(f"{actual_code}.svg")
            self.icon_cache[actual_code] = icon
            return icon
        except Exception as e:
            logger.error(f"Błąd ładowania ikony pogodowej {actual_code}: {e}")
            return self.hourglass_icon

    def update(self):
        """Aktualizuje stan ekranu"""
        now_time = time.time()
        
        # Aktualizacja pogody co 30 minut
        if now_time - self.last_weather_update >= self.weather_update_interval:
            try:
                self.weather_data = get_weather_data()
                self.last_weather_update = now_time
            except Exception as e:
                logger.error(f"Błąd aktualizacji pogody: {e}")

    def draw(self):
        """Rysuje zawartość ekranu"""
        super().draw()
        
        # Pobierz aktualny czas
        current_time = time.localtime()
        
        # Rysuj czas
        time_str = time.strftime("%H:%M", current_time)
        time_surface = self.font_large.render(time_str, True, COLORS["WHITE"])
        time_rect = time_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(time_surface, time_rect)
        
        # Rysuj datę
        date_str = time.strftime("%A, %d %B %Y", current_time)
        date_surface = self.font_date.render(date_str, True, COLORS["WHITE"])
        date_rect = date_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(date_surface, date_rect)
        
        # Rysuj pogodę
        if self.weather_data:
            # Temperatura
            temp_str = f"{self.weather_data['temp']}°C"
            temp_surface = self.font_temp.render(temp_str, True, COLORS["WHITE"])
            temp_rect = temp_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
            self.screen.blit(temp_surface, temp_rect)
            
            # Ikona pogody
            weather_icon = self.load_weather_icon(self.weather_data['icon'])
            if weather_icon:
                icon_rect = weather_icon.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
                self.screen.blit(weather_icon, icon_rect)
        else:
            # Animacja klepsydry
            now_time = time.time()
            if now_time - self.last_hourglass_flip >= self.hourglass_flip_interval:
                self.hourglass_rotating = True
                self.hourglass_rotate_start = now_time
                self.last_hourglass_flip = now_time
                self.hourglass_state = 1 - self.hourglass_state
            
            if self.hourglass_rotating:
                elapsed = now_time - self.hourglass_rotate_start
                if elapsed < self.hourglass_flip_duration:
                    progress = elapsed / self.hourglass_flip_duration
                    self.hourglass_angle = 180 * progress if self.hourglass_state == 1 else 180 * (1 - progress)
                else:
                    self.hourglass_rotating = False
                    self.hourglass_angle = 180 if self.hourglass_state == 1 else 0
            
            rotated_icon = pygame.transform.rotate(self.hourglass_icon, self.hourglass_angle)
            icon_rect = rotated_icon.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
            self.screen.blit(rotated_icon, icon_rect)

    def run(self):
        """Główna pętla ekranu zegara"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.FINGERDOWN:
                    self.start_y = event.y * SCREEN_HEIGHT
                elif event.type == pygame.FINGERUP:
                    end_y = event.y * SCREEN_HEIGHT
                    delta_y = end_y - self.start_y
                    if delta_y > 50:  # Przesunięcie w dół
                        return "player"
            
            self.update()
            self.draw()
            pygame.display.flip()
            pygame.time.Clock().tick(60)

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
    font_regular = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "Barlow-Regular.ttf")
    font_bold    = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "Barlow-Bold.ttf")

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
        path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", svg_filename)
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