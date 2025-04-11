import os
import subprocess
import time
import logging
import json
import shutil
import glob
from services.musicbrainz_cover import fetch_and_cache_cover

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
            active_state = state.get("active_state", False)
            should_switch_to_player = state.get("should_switch_to_player", False)
            should_switch_to_clock = state.get("should_switch_to_clock", False)
            logger.debug(f"State loaded: {state}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading state: {e}")
        init_state_file()

# Inicjalizacja pliku stanu przy starcie
init_state_file()

# Funkcja do zarządzania stanem ikony play/pause
def update_play_pause_icon():
    if active_state:
        # Jeśli muzyka jest odtwarzana, ustaw ikonę na pauzę
        logger.debug("Music is playing, setting icon to 'pause'.")
        # Kod do zmiany ikony na pauzę (np. aktualizacja UI)
    else:
        # Jeśli muzyka nie jest odtwarzana, ustaw ikonę na play
        logger.debug("Music is paused, setting icon to 'play'.")
        # Kod do zmiany ikony na play (np. aktualizacja UI)

# Function to read and fetch metadata from shairport-sync-metadata-reader
def get_current_track_info_shairport():
    """Pobiera informacje o aktualnie odtwarzanym utworze z shairport-sync-metadata-reader."""
    global last_title, last_artist, last_album, last_cover
    
    logger.debug("Starting to fetch track info from shairport-sync-metadata-reader.")
    try:
        proc = subprocess.Popen(
            ["shairport-sync-metadata-reader"],
            stdin=open(PIPE_PATH, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1
        )
        
        # Inicjalizacja zmiennych
        title = None
        artist = None
        album = None
        cover_path = None
        
        for line in proc.stdout:
            try:
                # Dekodowanie linii z obsługą błędów
                line = line.decode('utf-8', errors='replace').strip()
                logger.debug(f"Received line: {line}")
                
                if line.startswith("Title:"):
                    title = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Extracted Title: {title}")
                elif line.startswith("Artist:"):
                    artist = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Extracted Artist: {artist}")
                elif line.startswith("Album Name:"):
                    album = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Extracted Album: {album}")
                elif "Picture received" in line and "length" in line:
                    cover_path = get_latest_cover()
                    logger.debug(f"Cover path set to: {cover_path}")
                if title and artist and album:  # Jeśli wszystkie metadane są dostępne, zakończ pętlę
                    break
            except Exception as e:
                logger.error(f"Error processing line: {e}")
                continue
                
        proc.terminate()
        
        if not any([title, artist, album]):
            logger.debug("Brak metadanych w odpowiedzi")
            return None, None, None, None
            
        logger.debug(f"Pobrano metadane: {title} - {artist} - {album}")
        
        # Logika pobierania okładki
        # Jeśli mamy nową okładkę z Shairport, używamy jej
        if cover_path and os.path.isfile(cover_path):
            last_cover = cover_path
            logger.debug(f"Using cover from Shairport: {cover_path}")
        # Jeśli nie mamy nowej okładki, ale mamy poprzednią z Shairport, używamy jej
        elif last_cover and os.path.isfile(last_cover) and "shairport-sync" in last_cover:
            logger.debug(f"Using previous cover from Shairport: {last_cover}")
        # Jeśli nie mamy okładki z Shairport, próbujemy MusicBrainz
        else:
            last_cover = None
            logger.debug("No cover found from Shairport, trying MusicBrainz")
            if title and artist and album:
                cover_path = fetch_and_cache_cover(artist, album)
                if cover_path:
                    logger.debug(f"Found cover from MusicBrainz: {cover_path}")
                    last_cover = cover_path
                else:
                    logger.debug("No cover found in MusicBrainz, using default cover")
                    last_cover = DEFAULT_COVER
            else:
                logger.debug("No metadata available, using default cover")
                last_cover = DEFAULT_COVER

        last_title = title
        last_artist = artist
        last_album = album

        logger.debug(f"Metadata: Title={title}, Artist={artist}, Album={album}, Cover={last_cover}")
        return title, artist, album, last_cover
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania metadanych: {e}")
        return None, None, None, None

# Function to listen to shairport state and control UI changes
def read_shairport_metadata():
    """Czyta metadane z shairport-sync-metadata-reader."""
    logger.debug("Starting to read metadata from shairport-sync-metadata-reader.")
    try:
        proc = subprocess.Popen(
            ["shairport-sync-metadata-reader"],
            stdin=open(PIPE_PATH, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1
        )
        
        for line in proc.stdout:
            try:
                # Dekodowanie linii z obsługą błędów
                line = line.decode('utf-8', errors='replace').strip()
                logger.debug(f"Received line: {line}")
                
                if "Picture received" in line and "length" in line:
                    logger.debug("New cover art received")
                    update_cover_art()
                elif "Play" in line:
                    logger.debug("Playback started")
                    update_state("play")
                elif "Pause" in line:
                    logger.debug("Playback paused")
                    update_state("pause")
                elif "Stop" in line:
                    logger.debug("Playback stopped")
                    update_state("stop")
            except Exception as e:
                logger.error(f"Error processing line: {e}")
                continue
                
        proc.terminate()
    except Exception as e:
        logger.error(f"Error in read_shairport_metadata: {e}")

# Main function to start the listener
if __name__ == "__main__":
    logger.debug("Starting shairport listener")
    while True:
        read_shairport_metadata()
        time.sleep(1)