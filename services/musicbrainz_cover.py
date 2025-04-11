import os
import requests
import musicbrainzngs
from urllib.parse import quote_plus

# Konfiguracja MusicBrainz 
musicbrainzngs.set_useragent("HifiClock", "1.0", "yareckk@gmail.com")

COVER_DIR = os.path.join(os.path.dirname(__file__), "../assets/images")
DEFAULT_COVER = os.path.join(COVER_DIR, "cover.png")
CACHED_COVERS_DIR = os.path.join(COVER_DIR, "cache")

# Utwórz katalog cache jeśli nie istnieje
os.makedirs(CACHED_COVERS_DIR, exist_ok=True)

def sanitize_filename(s):
    return "_".join(quote_plus(s).split("+")).lower()

def get_cached_cover_path(artist, album):
    filename = sanitize_filename(f"{artist}_{album}") + ".jpg"
    return os.path.join(CACHED_COVERS_DIR, filename)

def get_cover_art_url(artist, album):
    try:
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=1)
        releases = result.get("release-list", [])
        if not releases:
            return None

        mbid = releases[0]["id"]
        cover_url = f"https://coverartarchive.org/release/{mbid}/front"
        response = requests.get(cover_url)
        if response.status_code == 200:
            return cover_url
    except Exception as e:
        print(f"[cover_service] Błąd pobierania okładki: {e}")
    return None

def download_cover(url, path):
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"[cover_service] Błąd zapisu okładki: {e}")
    return False

def fetch_and_cache_cover(artist, album):
    cached_path = get_cached_cover_path(artist, album)
    if os.path.exists(cached_path):
        print(f"[cover_service] Okładka z cache: {cached_path}")
        return cached_path

    url = get_cover_art_url(artist, album)
    if url and download_cover(url, cached_path):
        print(f"[cover_service] Okładka pobrana i zapisana: {cached_path}")
        return cached_path

    print("[cover_service] Brak okładki - użycie domyślnej")
    return DEFAULT_COVER

# Przykład użycia
if __name__ == "__main__":
    artist = "Anathema"
    album = "Weather Systems"
    path = fetch_and_cache_cover(artist, album)
    print(f"Ścieżka do okładki: {path}")
