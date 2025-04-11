import os

# Ścieżki
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
COMPONENTS_DIR = os.path.join(UI_DIR, "components")
FONTS_DIR = os.path.join(COMPONENTS_DIR, "fonts")
ICONS_DIR = os.path.join(COMPONENTS_DIR, "icons")
IMAGES_DIR = os.path.join(COMPONENTS_DIR, "images")

# Ustawienia ekranu
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

# Ustawienia Shairport
SHAIRPORT_PIPE_PATH = "/tmp/shairport-sync-metadata"
SHAIRPORT_COVER_CACHE_DIR = "/tmp/shairport-sync/.cache/coverart"
SHAIRPORT_STATE_FILE = "/tmp/shairport_state.json"

# Ustawienia pogody
WEATHER_CACHE_DIR = "/tmp/weather_cache"
WEATHER_CACHE_TIME = 900  # 15 minut w sekundach
OPENWEATHER_API_KEY = "6fb20261a5785a0f8bf5782d09a1b41d"  # OpenWeather API Key

# Ustawienia logowania
LOG_LEVEL = "DEBUG"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Kolory
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'SEMI_BLACK': (0, 0, 0, 128),
    'BACKGROUND': (30, 30, 30)
}

# Czcionki
FONTS = {
    'REGULAR': os.path.join(FONTS_DIR, "Barlow-Regular.ttf"),
    'BOLD': os.path.join(FONTS_DIR, "Barlow-Bold.ttf")
}

# Ikony
ICONS = {
    'PLAY': os.path.join(ICONS_DIR, "btn_play.svg"),
    'PAUSE': os.path.join(ICONS_DIR, "btn_pause.svg")
}

# Domyślne obrazy
DEFAULT_COVER = os.path.join(IMAGES_DIR, "cover.png") 