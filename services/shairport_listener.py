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
    start_time = time.time()
    
    # Inicjalizacja zmiennych
    title = None
    artist = None
    album = None
    cover_path = None
    
    while time.time() - start_time < 5.0:  # Dłuższy czas na próbę pobrania metadanych
        try:
            proc = subprocess.Popen(
                ["/usr/local/bin/shairport-sync-metadata-reader"],
                stdin=open(PIPE_PATH, "rb"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
            
            for line in proc.stdout:
                line = line.strip()
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
            proc.terminate()
            
            if title and artist and album:
                break  # Metadane pobrane, zakończ próbę
                
        except Exception as e:
            logger.error(f"Failed to retrieve metadata: {e}")
            return None, None, None, None
    
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

# Function to listen to shairport state and control UI changes
def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover, active_state, should_switch_to_player, should_switch_to_clock

    logger.debug("Starting read_shairport_metadata")
    start_time = time.time()  # Timeout handling

    try:
        # Sprawdź czy pipe istnieje
        if not os.path.exists(PIPE_PATH):
            logger.error(f"Pipe {PIPE_PATH} does not exist")
            return

        # Otwórz pipe w trybie non-blocking
        with open(PIPE_PATH, 'rb', buffering=0) as pipe:
            logger.debug("Pipe opened successfully")
            
            # Ustaw timeout na odczyt
            pipe_fd = pipe.fileno()
            import fcntl
            fcntl.fcntl(pipe_fd, fcntl.F_SETFL, os.O_NONBLOCK)
            
            # Próbuj czytać przez 5 sekund
            while time.time() - start_time < 5.0:
                try:
                    # Próbuj czytać dane
                    data = pipe.read(1024)
                    if data:
                        lines = data.decode('utf-8').split('\n')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                                
                            logger.debug(f"Received line: {line}")
                            
                            # Obsługa stanu odtwarzania
                            if "Pause" in line:
                                active_state = False
                                logger.debug("Playback paused")
                                save_state()
                            elif "Play" in line:
                                active_state = True
                                logger.debug("Playback started")
                                save_state()
                            
                            # Obsługa metadanych
                            if line.startswith("Title:"):
                                last_title = line.split(': "', 1)[1].strip('".')
                            elif line.startswith("Artist:"):
                                last_artist = line.split(': "', 1)[1].strip('".')
                            elif line.startswith("Album Name:"):
                                last_album = line.split(': "', 1)[1].strip('".')
                            
                            # Jeśli mamy wszystkie metadane, możemy zakończyć
                            if last_title and last_artist and last_album:
                                break
                    
                    # Krótka przerwa między próbami odczytu
                    time.sleep(0.1)
                    
                except BlockingIOError:
                    # Brak danych do odczytu, kontynuuj
                    time.sleep(0.1)
                    continue
                except Exception as e:
                    logger.error(f"Error reading from pipe: {e}")
                    break
                    
    except Exception as e:
        logger.error(f"Error in read_shairport_metadata: {e}")
    finally:
        logger.debug("Finished read_shairport_metadata")

# Main function to start the listener
if __name__ == "__main__":
    logger.debug("Starting shairport listener")
    while True:
        read_shairport_metadata()
        time.sleep(1)