import os

# Ścieżki do zasobów
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_DIR = os.path.join(BASE_DIR, "ui", "components")
IMAGES_DIR = os.path.join(COMPONENTS_DIR, "images")
ICONS_DIR = os.path.join(COMPONENTS_DIR, "icons")
FONTS_DIR = os.path.join(COMPONENTS_DIR, "fonts")

# Ustawienia ekranu
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FULLSCREEN = True

# Ustawienia API pogody
WEATHER_API_KEY = "6fb20261a5785a0f8bf5782d09a1b41d"
WEATHER_UPDATE_INTERVAL = 1800  # 30 minut
WEATHER_ICON_SIZE = (62, 48)

# Ustawienia logowania
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Kolory
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "GRAY": (100, 100, 100),
    "LIGHT_GRAY": (200, 200, 200),
    "DARK_GRAY": (51, 51, 51),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
}

# Ścieżki do ikon
ICONS = {
    "PLAY": os.path.join(ICONS_DIR, "play.svg"),
    "PAUSE": os.path.join(ICONS_DIR, "pause.svg"),
    "NEXT": os.path.join(ICONS_DIR, "next.svg"),
    "PREV": os.path.join(ICONS_DIR, "prev.svg"),
}

# Ścieżki do czcionek
FONTS = {
    "REGULAR": os.path.join(FONTS_DIR, "Barlow-Regular.ttf"),
    "BOLD": os.path.join(FONTS_DIR, "Barlow-Bold.ttf"),
}

# Domyślna okładka
DEFAULT_COVER = os.path.join(IMAGES_DIR, "cover.png") 