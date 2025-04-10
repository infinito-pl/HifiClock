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
    DEBUG = True
    output_path = "/tmp/shairport-sync-metadata"
    reader_path = "/usr/local/bin/shairport-sync-metadata-reader"

    try:
        proc = subprocess.run(
            [reader_path],
            stdin=open(output_path, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0  # krótkie uruchomienie
        )
        lines = proc.stdout.splitlines()
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] failed to run reader: {e}")
        return (None, None, None, None)

    title = artist = album = cover_path = None
    for line in lines:
        if DEBUG:
            print("[DEBUG]", line)
        if line.startswith("Title:"):
            title = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("Artist:"):
            artist = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("Album Name:"):
            album = line.split(":", 1)[1].strip().strip('"')
        elif "Picture received" in line and "length" in line:
            cover_path = "/tmp/shairport-sync/.cache/coverart/last_cover.jpg"

    return (title, artist, album, cover_path)
