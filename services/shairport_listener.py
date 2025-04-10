# shairport_listener.py

import subprocess
import re
import tempfile
import os

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"

_last = {
    "title": None,
    "artist": None,
    "album": None,
    "cover_path": None,
}

def update_shairport_metadata():
    """
    Reads metadata from shairport-sync-metadata pipe using the official reader.
    Returns: (title, artist, album, cover_path, updated: bool)
    """
    try:
        with subprocess.Popen(
            ["/usr/local/bin/shairport-sync-metadata-reader"],
            stdin=open(PIPE_PATH),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ) as proc:
            try:
                output, _ = proc.communicate(timeout=0.05)
            except subprocess.TimeoutExpired:
                proc.kill()
                output, _ = proc.communicate()

        updated = False

        if not output:
            print("[DEBUG] No output received from reader.")
            return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Album Name:"):
                _last["album"] = line.replace("Album Name:", "").strip().strip('"').strip(". ")
                updated = True
            elif line.startswith("Artist:"):
                _last["artist"] = line.replace("Artist:", "").strip().strip('"').strip(". ")
                updated = True
            elif line.startswith("Title:"):
                _last["title"] = line.replace("Title:", "").strip().strip('"').strip(". ")
                updated = True
            elif line.startswith("Picture received"):
                match = re.search(r"length (\d+) bytes", line)
                if match and int(match.group(1)) > 0:
                    with open(TMP_COVER, "wb") as f:
                        f.write(b"")  # Placeholder; actual writing must be handled via chunk parsing if needed
                    _last["cover_path"] = TMP_COVER
                    updated = True

        if updated:
            print(f"[DEBUG] Parsed Metadata — Title: {_last['title']}, Artist: {_last['artist']}, Album: {_last['album']}, Cover: {_last['cover_path']}")
        else:
            print("[DEBUG] Metadata not updated.")

        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], updated)

    except Exception as e:
        print(f"[DEBUG] Error reading metadata: {e}")
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)