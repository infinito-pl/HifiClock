import os

# Ścieżki do zasobów
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
COMPONENTS_DIR = os.path.join(UI_DIR, "components")
ICONS_DIR = os.path.join(COMPONENTS_DIR, "icons")
IMAGES_DIR = os.path.join(COMPONENTS_DIR, "images")
FONTS_DIR = os.path.join(COMPONENTS_DIR, "fonts")

# Ustawienia ekranu
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 60

# Ustawienia Shairport
SHAIRPORT_PIPE_PATH = "/tmp/shairport-sync-metadata"
SHAIRPORT_COVER_CACHE_DIR = "/tmp/shairport-sync/.cache/coverart"
SHAIRPORT_STATE_FILE = "/tmp/shairport-sync/.cache/state.json"

# Ustawienia pogody
WEATHER_API_KEY = "6fb20261a5785a0f8bf5782d09a1b41d"
WEATHER_UPDATE_INTERVAL = 1800  # 30 minut
WEATHER_ICON_SIZE = (100, 100)

# Ustawienia logowania
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Kolory
COLORS = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "GRAY": (128, 128, 128),
    "DARK_GRAY": (64, 64, 64),
    "LIGHT_GRAY": (192, 192, 192),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "BACKGROUND": (30, 30, 30),
    "SEMI_BLACK": (0, 0, 0, 128)
}

# Czcionki
FONTS = {
    "REGULAR": os.path.join(FONTS_DIR, "Barlow-Regular.ttf"),
    "BOLD": os.path.join(FONTS_DIR, "Barlow-Bold.ttf"),
    "MEDIUM": os.path.join(FONTS_DIR, "Barlow-Regular.ttf")  # Używamy Regular zamiast Medium
}

# Ikony
ICONS = {
    "PLAY": os.path.join(ICONS_DIR, "btn_play.svg"),
    "PAUSE": os.path.join(ICONS_DIR, "btn_pause.svg"),
    "NEXT": os.path.join(ICONS_DIR, "btn_next.svg"),
    "PREV": os.path.join(ICONS_DIR, "btn_prev.svg"),
}

# Domyślna okładka
DEFAULT_COVER = os.path.join(IMAGES_DIR, "default_cover.jpg") 