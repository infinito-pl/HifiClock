# metadata_shairport.py
#
# 1) fetches data from shairport-sync-metadata-reader
# 2) returns title, artist, album and cover path
#
import os
import base64
import xml.etree.ElementTree as ET
import select
import subprocess

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"  # lub .png – w trakcie parsowania sprawdzisz magic number

_last = {"title": None, "artist": None, "album": None, "cover_path": None}

def get_current_track_info_shairport():
    import subprocess
    import time
    import os

    DEBUG = True
    output_path = "/tmp/shairport-sync-metadata"
    reader_path = "/usr/local/bin/shairport-sync-metadata-reader"

    title = artist = album = cover_path = None

    try:
        proc = subprocess.Popen(
            [reader_path],
            stdin=open(output_path, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        start_time = time.time()
        for line in proc.stdout:
            line = line.strip()
            if DEBUG:
                print("[DEBUG]", line)

            if line.startswith("Title:"):
                title = line.split(': "', 1)[1].strip('".')
            elif line.startswith("Artist:"):
                artist = line.split(': "', 1)[1].strip('".')
            elif line.startswith("Album Name:"):
                album = line.split(': "', 1)[1].strip('".')
            elif "Picture received" in line and "length" in line:
                cover_path = "/tmp/shairport-sync/.cache/coverart/last_cover.jpg"

            if time.time() - start_time > 1.0:
                break

        proc.terminate()

    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Failed to run reader: {e}")
        return (None, None, None, None)

    # Dodajemy sprawdzenie, czy okładka istnieje
    if cover_path and os.path.isfile(cover_path):
        print(f"[DEBUG] Found cover: {cover_path}")
    else:
        cover_path = None
        print("[DEBUG] No cover found.")

    return (title, artist, album, cover_path)
