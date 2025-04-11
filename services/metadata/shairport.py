import os
import subprocess
import time
import json
import glob
from config import SHAIRPORT_PIPE_PATH, SHAIRPORT_COVER_CACHE_DIR, SHAIRPORT_STATE_FILE, DEFAULT_COVER
from utils.logging import logger
from services.metadata.musicbrainz import fetch_and_cache_cover

# Global variables for metadata tracking
last_title = last_artist = last_album = last_cover = None
active_state = False

def get_latest_cover():
    """Znajduje najnowszą okładkę w katalogu cache."""
    try:
        covers = glob.glob(os.path.join(SHAIRPORT_COVER_CACHE_DIR, "cover-*.jpg"))
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
        os.makedirs(SHAIRPORT_COVER_CACHE_DIR, exist_ok=True)
        logger.debug(f"Created cover cache directory: {SHAIRPORT_COVER_CACHE_DIR}")
    except Exception as e:
        logger.error(f"Error creating cover cache directory: {e}")

def init_state_file():
    """Inicjalizuje plik stanu."""
    if not os.path.exists(SHAIRPORT_STATE_FILE):
        logger.debug(f"Creating state file: {SHAIRPORT_STATE_FILE}")
        default_state = {
            "active_state": False
        }
        with open(SHAIRPORT_STATE_FILE, 'w') as f:
            json.dump(default_state, f)
        logger.debug("State file initialized with default values")

def save_state():
    """Zapisuje stan do pliku."""
    state = {
        "active_state": active_state
    }
    with open(SHAIRPORT_STATE_FILE, 'w') as f:
        json.dump(state, f)
    logger.debug(f"State saved: {state}")

def load_state():
    """Wczytuje stan z pliku."""
    global active_state
    try:
        with open(SHAIRPORT_STATE_FILE, 'r') as f:
            state = json.load(f)
            active_state = state.get("active_state", False)
            logger.debug(f"State loaded: {state}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading state: {e}")
        init_state_file()

def get_current_track_info():
    """Pobiera informacje o aktualnym utworze."""
    global last_title, last_artist, last_album, last_cover
    
    try:
        proc = subprocess.Popen(
            ['shairport-sync-metadata-reader'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(timeout=1)
        
        if stderr:
            logger.error(f"Błąd shairport-sync-metadata-reader: {stderr}")
            return None, None, None, None
            
        # Przetwarzanie metadanych
        title = artist = album = None
        for line in stdout.splitlines():
            if "title:" in line:
                title = line.split("title:")[1].strip()
            elif "artist:" in line:
                artist = line.split("artist:")[1].strip()
            elif "album:" in line:
                album = line.split("album:")[1].strip()
                
        if title and artist and album:
            last_title, last_artist, last_album = title, artist, album
            cover_path = get_latest_cover()
            if not cover_path:
                cover_path = fetch_and_cache_cover(artist, album)
            last_cover = cover_path or DEFAULT_COVER
            return title, artist, album, last_cover
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout przy pobieraniu metadanych")
    except Exception as e:
        logger.error(f"Błąd przy pobieraniu metadanych: {e}")
        
    return last_title, last_artist, last_album, last_cover

# Inicjalizacja przy imporcie
init_cover_cache()
init_state_file()
load_state() 