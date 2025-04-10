# shairport_listener.py

import subprocess
import time
import tempfile
import os

COVER_ART_PATH = "/tmp/shairport-sync/.cache/coverart/"

last_title = None
last_artist = None
last_album = None
last_cover = None

def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover

    try:
        proc = subprocess.Popen(
            ["shairport-sync-metadata-reader", "--raw", "/tmp/shairport-sync-metadata"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )

        title = None
        artist = None
        album = None
        cover_path = None

        start_time = time.time()
        timeout = 2

        while True:
            if time.time() - start_time > timeout:
                proc.kill()
                break

            line = proc.stdout.readline()
            if not line:
                continue

            line = line.strip()

            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip().strip("\"")
            elif line.startswith("Artist:"):
                artist = line.replace("Artist:", "").strip().strip("\"")
            elif line.startswith("Album Name:"):
                album = line.replace("Album Name:", "").strip().strip("\"")
            elif "Picture received, length" in line:
                try:
                    files = sorted(os.listdir(COVER_ART_PATH), key=lambda x: os.path.getmtime(os.path.join(COVER_ART_PATH, x)), reverse=True)
                    if files:
                        cover_path = os.path.join(COVER_ART_PATH, files[0])
                except:
                    pass

        if title and artist and album:
            updated = (title != last_title or artist != last_artist or album != last_album or cover_path != last_cover)
            last_title = title
            last_artist = artist
            last_album = album
            last_cover = cover_path
            return title, artist, album, cover_path, updated

        return last_title, last_artist, last_album, last_cover, False

    except Exception as e:
        print("[shairport_listener] Błąd:", e)
        return last_title, last_artist, last_album, last_cover, False
