# shairport_listener.py
import subprocess
import os
import time

# Globalna zmienna do przechowywania metadanych
current_metadata = {
    'title': None,
    'artist': None,
    'album': None,
    'cover_path': None
}

def update_metadata(title, artist, album, cover_path):
    """Aktualizuje metadane w globalnej zmiennej"""
    current_metadata['title'] = title
    current_metadata['artist'] = artist
    current_metadata['album'] = album
    current_metadata['cover_path'] = cover_path

def read_shairport_metadata():
    """Funkcja nasłuchująca zmiany metadanych"""
    global current_metadata

    try:
        proc = subprocess.Popen(
            ["/usr/local/bin/shairport-sync-metadata-reader"],
            stdin=open("/tmp/shairport-sync-metadata", "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        start_time = time.time()

        while True:
            line = proc.stdout.readline()
            if not line:
                continue

            line = line.strip()

            if "[DEBUG] Enter Active State" in line:
                active_state = True
                print("[DEBUG] Entered Active State. Start reading metadata.")
                continue
            elif "[DEBUG] Exit Active State" in line:
                active_state = False
                print("[DEBUG] Exit Active State. Stopping metadata reading.")
                break

            if active_state:
                title = artist = album = cover_path = None

                if line.startswith("Title:"):
                    title = line.split(': "', 1)[1].strip('".')
                elif line.startswith("Artist:"):
                    artist = line.split(': "', 1)[1].strip('".')
                elif line.startswith("Album Name:"):
                    album = line.split(': "', 1)[1].strip('".')
                elif "Picture received" in line and "length" in line:
                    cover_path = "/tmp/shairport-sync/.cache/coverart/last_cover.jpg"

                if title and artist and album:
                    # Zaktualizuj metadane tylko wtedy, gdy wszystkie dane są dostępne
                    update_metadata(title, artist, album, cover_path)

            # Czekaj na nowe dane, odczytuj metadane co 0.1 sekundy
            if time.time() - start_time > 0.1:
                start_time = time.time()

    except Exception as e:
        print(f"[DEBUG] Failed to run reader: {e}")