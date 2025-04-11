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
    """
    Pobiera aktualne informacje o utworze z shairport-sync-metadata-reader.
    Zwraca krotkę (title, artist, album, cover_path) lub (None, None, None, None) w przypadku błędu.
    """
    global last_title, last_artist, last_album, last_cover
    
    logger.debug("Starting to fetch track info from shairport-sync-metadata-reader.")
    
    try:
        # Uruchom proces z timeoutem
        proc = subprocess.Popen(
            ["shairport-sync-metadata-reader"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Ustaw timeout na 5 sekund
        try:
            stdout, stderr = proc.communicate(timeout=5)
            if stderr:
                logger.error(f"Błąd shairport-sync-metadata-reader: {stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Timeout podczas odczytu metadanych")
            proc.kill()
            stdout, stderr = proc.communicate()
            # Jeśli mamy poprzednie metadane, zwróć je zamiast None
            if last_title and last_artist and last_album:
                logger.debug("Używam poprzednich metadanych z powodu timeoutu")
                return last_title, last_artist, last_album, last_cover
            return None, None, None, None
        
        # Przetwarzaj dane tylko jeśli mamy wyjście
        if stdout:
            title = None
            artist = None
            album = None
            cover_path = None
            
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("title:"):
                    title = line[6:].strip()
                elif line.startswith("artist:"):
                    artist = line[7:].strip()
                elif line.startswith("album:"):
                    album = line[6:].strip()
                elif line.startswith("cover_path:"):
                    cover_path = line[11:].strip()
            
            logger.debug(f"Otrzymane metadane: title={title}, artist={artist}, album={album}")
            
            # Jeśli mamy nową okładkę z Shairport, używamy jej
            if cover_path and os.path.isfile(cover_path):
                last_cover = cover_path
                logger.debug(f"Używam okładki z Shairport: {cover_path}")
            # Jeśli nie mamy nowej okładki, ale mamy poprzednią z Shairport, używamy jej
            elif last_cover and os.path.isfile(last_cover) and "shairport-sync" in last_cover:
                logger.debug(f"Używam poprzedniej okładki z Shairport: {last_cover}")
            # Jeśli nie mamy okładki z Shairport, próbujemy MusicBrainz
            else:
                last_cover = None
                logger.debug("Nie znaleziono okładki w Shairport, próbuję MusicBrainz")
                if title and artist and album:
                    cover_path = fetch_and_cache_cover(artist, album)
                    if cover_path:
                        logger.debug(f"Znaleziono okładkę w MusicBrainz: {cover_path}")
                        last_cover = cover_path
                    else:
                        logger.debug("Nie znaleziono okładki w MusicBrainz, używam domyślnej")
                        last_cover = DEFAULT_COVER
                else:
                    logger.debug("Brak metadanych, używam domyślnej okładki")
                    last_cover = DEFAULT_COVER

            last_title = title
            last_artist = artist
            last_album = album

            logger.debug(f"Metadane: Title={title}, Artist={artist}, Album={album}, Cover={last_cover}")
            return title, artist, album, last_cover
            
    except Exception as e:
        logger.error(f"Błąd podczas pobierania metadanych: {e}")
        # Jeśli mamy poprzednie metadane, zwróć je zamiast None
        if last_title and last_artist and last_album:
            logger.debug("Używam poprzednich metadanych z powodu błędu")
            return last_title, last_artist, last_album, last_cover
    
    return None, None, None, None

# Function to listen to shairport state and control UI changes
def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover, active_state, should_switch_to_player, should_switch_to_clock

    logger.debug("Starting read_shairport_metadata")
    start_time = time.time()  # Timeout handling

    while time.time() - start_time < 5.0:
        try:
            logger.debug("Opening pipe for reading")
            proc = subprocess.Popen(
                ["/usr/local/bin/shairport-sync-metadata-reader"],
                stdin=open(PIPE_PATH, "rb"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
            logger.debug("Pipe opened successfully")

            for line in proc.stdout:
                line = line.strip()
                logger.debug(f"Processing line: {line}")

                if "Enter Active State" in line or "Play -- first frame received" in line or "Resume" in line:
                    logger.debug("Detected play/resume event")
                    active_state = True
                    logger.debug(f"Setting active_state to {active_state}")
                    should_switch_to_player = True
                    should_switch_to_clock = False
                    save_state()
                    logger.debug("Shairport entered active state")

                elif "Exit Active State" in line or "Pause" in line or "Stop" in line:
                    logger.debug("Detected pause/stop event")
                    active_state = False
                    logger.debug(f"Setting active_state to {active_state}")
                    should_switch_to_player = False
                    should_switch_to_clock = True
                    save_state()
                    logger.debug("Shairport exited active state")

                # Regularly fetch metadata when active
                if active_state:
                    logger.debug("Active state is True, fetching metadata")
                    title, artist, album, cover_path = get_current_track_info_shairport()
                    if title != last_title or artist != last_artist or album != last_album:
                        last_title, last_artist, last_album, last_cover = title, artist, album, cover_path
                        logger.debug("Metadata updated")

                # Timeout after a set period
                if time.time() - start_time > 5.0:
                    logger.debug("Timeout reached, breaking loop")
                    break

            proc.terminate()
            logger.debug("Process terminated")

        except Exception as e:
            logger.error(f"Error in reading shairport metadata: {e}")
        time.sleep(3)  # Wait for 3 seconds before the next attempt
    logger.debug("Exiting read_shairport_metadata")

# Main function to start the listener
if __name__ == "__main__":
    logger.debug("Starting shairport listener")
    while True:
        read_shairport_metadata()
        time.sleep(1)