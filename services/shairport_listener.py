import os
import subprocess
import time
import logging
import json
import shutil
import glob
import threading
from services.musicbrainz_cover import fetch_and_cache_cover

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,  # Poziom logowania
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Ścieżki do plików
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_FILE = os.path.join(BASE_DIR, "state", "playback_state.json")
DEFAULT_COVER = os.path.join(BASE_DIR, "assets", "images", "cover.png")
PIPE_PATH = "/tmp/shairport-sync-metadata"
COVER_CACHE_DIR = "/tmp/shairport-sync/.cache/coverart"

# Lock do synchronizacji dostępu do zmiennych globalnych
state_lock = threading.Lock()
metadata_lock = threading.Lock()

# Global variables for metadata tracking
last_title = last_artist = last_album = last_cover = None
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
    if not os.path.exists(STATE_FILE):
        logger.debug(f"Creating state file: {STATE_FILE}")
        default_state = {
            "active_state": False,
            "should_switch_to_player": False,
            "should_switch_to_clock": False
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(default_state, f)
        logger.debug("State file initialized with default values")

def save_state():
    with state_lock:
        state = {
            "active_state": active_state,
            "should_switch_to_player": should_switch_to_player,
            "should_switch_to_clock": should_switch_to_clock
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        logger.debug(f"State saved: {state}")

def load_state():
    global active_state, should_switch_to_player, should_switch_to_clock
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            with state_lock:
                active_state = state.get("active_state", False)
                should_switch_to_player = state.get("should_switch_to_player", False)
                should_switch_to_clock = state.get("should_switch_to_clock", False)
            logger.debug(f"State loaded: {state}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading state: {e}")
        init_state_file()

# Inicjalizacja pliku stanu przy starcie
init_state_file()

def get_current_track_info_shairport():
    """Pobiera aktualne informacje o utworze w sposób bezpieczny dla wątków."""
    global last_title, last_artist, last_album, last_cover
    
    with metadata_lock:
        return last_title, last_artist, last_album, last_cover

def update_metadata(title, artist, album, cover_path):
    """Aktualizuje metadane w sposób bezpieczny dla wątków."""
    global last_title, last_artist, last_album, last_cover
    
    with metadata_lock:
        if title: last_title = title
        if artist: last_artist = artist
        if album: last_album = album
        if cover_path: last_cover = cover_path
        
        logger.debug(f"Zaktualizowano metadane: Title={last_title}, Artist={last_artist}, Album={last_album}, Cover={last_cover}")

def update_state(new_active_state, new_should_switch_to_player, new_should_switch_to_clock):
    """Aktualizuje stan odtwarzania w sposób bezpieczny dla wątków."""
    global active_state, should_switch_to_player, should_switch_to_clock
    
    with state_lock:
        active_state = new_active_state
        should_switch_to_player = new_should_switch_to_player
        should_switch_to_clock = new_should_switch_to_clock
        logger.debug(f"Zaktualizowano stan: active_state={active_state}, should_switch_to_player={should_switch_to_player}, should_switch_to_clock={should_switch_to_clock}")
        save_state()

def read_shairport_metadata():
    """Główna funkcja nasłuchująca metadane z Shairport."""
    global last_title, last_artist, last_album, last_cover
    
    logger.debug("=== Rozpoczynam nasłuchiwanie Shairport ===")
    
    while True:
        try:
            proc = subprocess.Popen(
                ["/usr/local/bin/shairport-sync-metadata-reader"],
                stdin=open(PIPE_PATH, "rb"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
            
            title = artist = album = cover_path = None
            
            for line in proc.stdout:
                line = line.strip()
                logger.debug(f"Otrzymano linię: {line}")
                
                if line.startswith("Title:"):
                    title = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Wydobyto tytuł: {title}")
                elif line.startswith("Artist:"):
                    artist = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Wydobyto artystę: {artist}")
                elif line.startswith("Album Name:"):
                    album = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Wydobyto album: {album}")
                elif "Picture received" in line and "length" in line:
                    cover_path = get_latest_cover()
                    logger.debug(f"Ustawiono ścieżkę okładki: {cover_path}")
                elif "Play" in line and "first frame received" in line:
                    logger.debug("Wykryto rozpoczęcie odtwarzania")
                    update_state(True, True, False)
                elif "Pause" in line:
                    logger.debug("Wykryto pauzę")
                    update_state(False, False, True)
                
                if title and artist and album:
                    update_metadata(title, artist, album, cover_path)
            
            proc.terminate()
            time.sleep(0.1)  # Krótka przerwa przed kolejną próbą
            
        except Exception as e:
            logger.error(f"Błąd podczas nasłuchiwania metadanych: {e}")
            time.sleep(1)  # Dłuższa przerwa w przypadku błędu

def should_switch_to_player_screen():
    """Sprawdza czy należy przełączyć na ekran odtwarzacza."""
    with state_lock:
        result = should_switch_to_player
        if result:
            should_switch_to_player = False
            save_state()
        return result

def should_switch_to_clock_screen():
    """Sprawdza czy należy przełączyć na ekran zegara."""
    with state_lock:
        result = should_switch_to_clock
        if result:
            should_switch_to_clock = False
            save_state()
        return result

def reset_switch_flags():
    """Resetuje flagi przełączania ekranów."""
    with state_lock:
        should_switch_to_player = False
        should_switch_to_clock = False
        save_state()
        logger.debug("Zresetowano flagi przełączania ekranów")

# Main function to start the listener
if __name__ == "__main__":
    logger.debug("Starting shairport listener")
    read_shairport_metadata()  # Uruchom bezpośrednio, bez dodatkowej pętli