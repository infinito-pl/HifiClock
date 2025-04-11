import os
import subprocess
import time
import json
import glob
import logging
import requests
from config import SHAIRPORT_PIPE_PATH, SHAIRPORT_COVER_CACHE_DIR, SHAIRPORT_STATE_FILE, DEFAULT_COVER
from utils.logging import logger
from services.metadata.musicbrainz import fetch_and_cache_cover

# Global variables for metadata tracking
last_title = last_artist = last_album = last_cover = None
active_state = False

# Globalne zmienne do przechowywania aktualnego stanu
global_title = None
global_artist = None
global_album = None
global_cover_path = None
global_is_playing = False

def get_latest_cover():
    """Znajduje najnowszą okładkę w katalogu cache."""
    try:
        if not os.path.exists(SHAIRPORT_COVER_CACHE_DIR):
            return None
        
        files = [f for f in os.listdir(SHAIRPORT_COVER_CACHE_DIR) if f.endswith('.jpg')]
        if not files:
            return None
        
        # Sortuj pliki po czasie modyfikacji
        files.sort(key=lambda x: os.path.getmtime(os.path.join(SHAIRPORT_COVER_CACHE_DIR, x)))
        return os.path.join(SHAIRPORT_COVER_CACHE_DIR, files[-1])
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania okładki: {e}")
        return None

def init_cover_cache():
    """Inicjalizuje katalog cache na okładki."""
    try:
        if not os.path.exists(SHAIRPORT_COVER_CACHE_DIR):
            os.makedirs(SHAIRPORT_COVER_CACHE_DIR)
            logger.info(f"Utworzono katalog cache: {SHAIRPORT_COVER_CACHE_DIR}")
    except Exception as e:
        logger.error(f"Błąd podczas inicjalizacji cache: {e}")

def init_state_file():
    """Inicjalizuje plik stanu jeśli nie istnieje."""
    try:
        if not os.path.exists(SHAIRPORT_STATE_FILE):
            with open(SHAIRPORT_STATE_FILE, 'w') as f:
                json.dump({"active_state": False}, f)
    except Exception as e:
        logger.error(f"Błąd podczas inicjalizacji pliku stanu: {e}")

def save_state(active):
    """Zapisuje stan do pliku."""
    try:
        with open(SHAIRPORT_STATE_FILE, 'w') as f:
            json.dump({"active_state": active}, f)
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania stanu: {e}")

def load_state():
    """Wczytuje stan z pliku."""
    try:
        with open(SHAIRPORT_STATE_FILE, 'r') as f:
            state = json.load(f)
            return state.get("active_state", False)
    except Exception as e:
        logger.error(f"Błąd podczas wczytywania stanu: {e}")
        return False

def read_shairport_metadata():
    """Odczytuje metadane z potoku Shairport."""
    try:
        if not os.path.exists(SHAIRPORT_PIPE_PATH):
            logger.warning(f"Potok Shairport nie istnieje: {SHAIRPORT_PIPE_PATH}")
            return None, None, None, None, False

        # Użyj timeout dla subprocess
        result = subprocess.run(
            ['shairport-sync-metadata-reader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.error(f"Błąd odczytu metadanych: {result.stderr}")
            return None, None, None, None, False

        metadata = {}
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        title = metadata.get('title', '')
        artist = metadata.get('artist', '')
        album = metadata.get('album', '')
        cover_path = get_latest_cover()
        is_playing = bool(title and artist)  # Uproszczona logika

        return title, artist, album, cover_path, is_playing

    except subprocess.TimeoutExpired:
        logger.error("Timeout podczas odczytu metadanych")
        return None, None, None, None, False
    except Exception as e:
        logger.error(f"Błąd podczas odczytu metadanych: {e}")
        return None, None, None, None, False

def get_current_track_info():
    """Pobiera informacje o aktualnym utworze."""
    global global_title, global_artist, global_album, global_cover_path, global_is_playing
    
    try:
        title, artist, album, cover_path, is_playing = read_shairport_metadata()
        
        # Aktualizuj globalne zmienne tylko jeśli metadane się zmieniły
        if (title != global_title or artist != global_artist or 
            album != global_album or cover_path != global_cover_path or 
            is_playing != global_is_playing):
            
            global_title = title
            global_artist = artist
            global_album = album
            global_cover_path = cover_path
            global_is_playing = is_playing
            
            # Zapisz stan
            save_state(is_playing)
            
            logger.debug(f"Zaktualizowano metadane: {title} - {artist}")
        
        return global_title, global_artist, global_album, global_cover_path
    
    except Exception as e:
        logger.error(f"Błąd podczas pobierania informacji o utworze: {e}")
        return global_title, global_artist, global_album, global_cover_path

# Inicjalizacja przy imporcie
init_cover_cache()
init_state_file()
load_state() 