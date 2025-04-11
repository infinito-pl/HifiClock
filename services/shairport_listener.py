import os
import subprocess
import time
import logging
import json
import shutil
import glob
from services.musicbrainz_cover import fetch_and_cache_cover
import threading
from pathlib import Path

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,  # Poziom logowania
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Global variables for metadata tracking
last_title = last_artist = last_album = last_cover = None
active_state = False
should_switch_to_player = False
should_switch_to_clock = False

PIPE_PATH = "/tmp/shairport-sync-metadata"
COVER_CACHE_DIR = "/tmp/shairport-sync/.cache/coverart"
STATE_FILE = "/tmp/shairport_state.json"
DEFAULT_COVER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images", "cover.png")

# Ścieżki do plików
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_FILE = os.path.join(BASE_DIR, "state", "playback_state.json")
DEFAULT_COVER = os.path.join(BASE_DIR, "assets", "images", "cover.png")

# Zmienne globalne
active_state = False
should_switch_to_player = False
should_switch_to_clock = False
last_metadata = {
    "title": "",
    "artist": "",
    "album": "",
    "cover": DEFAULT_COVER
}

def get_latest_cover():
    """Znajduje najnowszą okładkę w katalogu cache."""
    try:
        covers = glob.glob(os.path.join(COVER_CACHE_DIR, "cover-*.jpg"))
        if covers:
            latest_cover = max(covers, key=os.path.getctime)
            logger.debug(f"Found latest cover: {latest_cover}")
            return latest_cover
    except Exception as e:
        logger.error(f"Error finding latest cover: {e}")
    return None

def init_cover_cache():
    """Inicjalizuje katalog cache na okładki."""
    try:
        os.makedirs(COVER_CACHE_DIR, exist_ok=True)
        logger.debug(f"Created cover cache directory: {COVER_CACHE_DIR}")
    except Exception as e:
        logger.error(f"Error creating cover cache directory: {e}")

def init_state_file():
    """Inicjalizuje plik stanu z domyślnymi wartościami."""
    try:
        # Utwórz katalog state jeśli nie istnieje
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        
        if not os.path.exists(STATE_FILE):
            logger.debug(f"Tworzenie pliku stanu: {STATE_FILE}")
            default_state = {
                "active_state": False,
                "should_switch_to_player": False,
                "should_switch_to_clock": False,
                "last_metadata": last_metadata
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(default_state, f)
            logger.debug("Plik stanu zainicjalizowany z wartościami domyślnymi")
    except Exception as e:
        logger.error(f"Błąd podczas inicjalizacji pliku stanu: {e}")

def save_state():
    """Zapisuje aktualny stan odtwarzania do pliku."""
    try:
        state = {
            "active": active_state,
            "metadata": last_metadata
        }
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        logger.debug(f"Zapisano stan: {state}")
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania stanu: {e}")

def load_state():
    """Wczytuje stan odtwarzania z pliku."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                global active_state, last_metadata
                active_state = state.get("active", False)
                last_metadata = state.get("metadata", last_metadata)
                logger.debug(f"Wczytano stan: {state}")
    except Exception as e:
        logger.error(f"Błąd podczas wczytywania stanu: {e}")

# Inicjalizacja pliku stanu przy starcie
init_state_file()

# Funkcja do zarządzania stanem ikony play/pause
def update_play_pause_icon():
    global should_switch_to_player, should_switch_to_clock
    if active_state:
        logger.debug("Music is playing, setting icon to 'pause' and switching to player screen")
        should_switch_to_player = True
        should_switch_to_clock = False
    else:
        logger.debug("Music is paused, setting icon to 'play' and switching to clock screen")
        should_switch_to_player = False
        should_switch_to_clock = True
    save_state()

# Function to read and fetch metadata from shairport-sync-metadata-reader
def get_current_track_info_shairport():
    """Zwraca informacje o aktualnie odtwarzanym utworze."""
    return (
        last_metadata["title"],
        last_metadata["artist"],
        last_metadata["album"],
        last_metadata["cover"]
    )

def read_shairport_metadata():
    """Odczytuje metadane z Shairport w pętli."""
    global active_state, should_switch_to_player, should_switch_to_clock, last_metadata
    
    # Inicjalizacja stanu
    load_state()
    
    # Ścieżka do pliku metadanych Shairport
    metadata_file = "/tmp/shairport-sync-metadata"
    
    while True:
        try:
            if not os.path.exists(metadata_file):
                logger.debug("Oczekiwanie na plik metadanych...")
                time.sleep(1)
                continue
                
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                
            # Aktualizacja stanu odtwarzania
            new_active_state = metadata.get("state", {}).get("play_state") == "playing"
            
            if new_active_state != active_state:
                active_state = new_active_state
                if active_state:
                    should_switch_to_player = True
                    should_switch_to_clock = False
                else:
                    should_switch_to_player = False
                    should_switch_to_clock = True
                logger.debug(f"Zmiana stanu odtwarzania: {active_state}")
            
            # Aktualizacja metadanych
            new_metadata = {
                "title": metadata.get("item", {}).get("title", ""),
                "artist": metadata.get("item", {}).get("artist", ""),
                "album": metadata.get("item", {}).get("album", ""),
                "cover": metadata.get("item", {}).get("cover", DEFAULT_COVER)
            }
            
            if new_metadata != last_metadata:
                last_metadata = new_metadata
                logger.debug(f"Nowe metadane: {new_metadata}")
            
            # Zapisanie stanu
            save_state()
            
        except Exception as e:
            logger.error(f"Błąd podczas odczytu metadanych: {e}")
            time.sleep(1)
            continue
            
        time.sleep(0.5)  # Krótszy interwał sprawdzania

def get_active_state():
    """Zwraca aktualny stan odtwarzania."""
    return active_state

def should_switch_to_player_screen():
    """Sprawdza czy należy przełączyć się na ekran odtwarzacza."""
    return should_switch_to_player

def should_switch_to_clock_screen():
    """Sprawdza czy należy przełączyć się na ekran zegara."""
    return should_switch_to_clock

def reset_switch_flags():
    """Resetuje flagi przełączania ekranów."""
    global should_switch_to_player, should_switch_to_clock
    should_switch_to_player = False
    should_switch_to_clock = False
    save_state()

# Main function to start the listener
if __name__ == "__main__":
    logger.debug("Starting shairport listener")
    while True:
        read_shairport_metadata()
        time.sleep(1)