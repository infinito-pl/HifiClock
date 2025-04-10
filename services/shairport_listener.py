import subprocess
import re
from collections import defaultdict

PIPE_PATH = "/tmp/shairport-sync-metadata"
READER_BIN = "/usr/local/bin/shairport-sync-metadata-reader"

def parse_metadata_line(line):
    """Parsuje pojedynczą linię metadanych."""
    if ':' in line:
        key, value = line.split(':', 1)
        return key.strip(), value.strip().strip('"')
    elif 'Picture received' in line:
        match = re.search(r"length (\d+) bytes", line)
        if match:
            return 'cover_path', "/tmp/cover.jpg"
    return None, None

def read_metadata():
    """Czyta metadane ze strumienia i zwraca jako słownik."""
    metadata = defaultdict(lambda: None)
    try:
        with subprocess.Popen(
            [READER_BIN, PIPE_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        ) as proc:
            for line in proc.stdout:
                line = line.strip()
                key, value = parse_metadata_line(line)
                if key:
                    metadata[key.lower()] = value
                if key == "title":
                    break  # zakończ po otrzymaniu tytułu — zakładamy, że dane są kompletne
    except FileNotFoundError:
        print(f"[ERROR] Nie znaleziono {READER_BIN}")
    except Exception as e:
        print(f"[ERROR] Błąd podczas czytania metadanych: {e}")

    return {
        "title": metadata.get("title"),
        "artist": metadata.get("artist"),
        "album": metadata.get("album name"),
        "cover_path": metadata.get("cover_path"),
    }

if __name__ == "__main__":
    print("[DEBUG] Czytam metadane z Shairport Sync...")
    data = read_metadata()
    print("[DEBUG] Odczytane metadane:", data)