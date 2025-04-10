import subprocess
import re
import tempfile
import os
import time
import threading
from queue import Queue, Empty

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"

_last = {
    "title": None,
    "artist": None,
    "album": None,
    "cover_path": None,
}

_metadata_queue = Queue()
_metadata_thread = None
_listener_started = False

last_metadata_update = 0
metadata_refresh_interval = 2  # seconds
empty_attempts = 0
max_empty_attempts = 3

def start_metadata_listener():
    global _metadata_thread, _listener_started
    if _listener_started:
        return
    _listener_started = True

    def listener():
        with subprocess.Popen(
            ["/usr/local/bin/shairport-sync-metadata-reader"],
            stdin=open(PIPE_PATH),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        ) as proc:
            for line in proc.stdout:
                _metadata_queue.put(line.strip())

    _metadata_thread = threading.Thread(target=listener, daemon=True)
    _metadata_thread.start()

def update_shairport_metadata():
    start_metadata_listener()
    global _last, empty_attempts

    lines = []
    while _metadata_queue.qsize() > 100:
        try:
            _metadata_queue.get_nowait()
        except Empty:
            break

    try:
        while True:
            line = _metadata_queue.get_nowait()
            lines.append(line)
    except Empty:
        pass

    if not lines:
        print("[DEBUG] Brak danych z kolejki.")
        empty_attempts += 1
        if empty_attempts < max_empty_attempts:
            print(f"[DEBUG] {empty_attempts}x brak danych — zachowuję poprzednie.")
            return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)
        else:
            print(f"[DEBUG] Osiągnięto limit {max_empty_attempts} pustych prób — czyszczę metadane.")
            _last = {"title": None, "artist": None, "album": None, "cover_path": None}
            empty_attempts = 0
            return (None, None, None, None, True)

    if all(key not in "\n".join(lines) for key in ["Title:", "Artist:", "Album Name:", "Picture received"]):
        print("[DEBUG] Pusty output bez metadanych — ignoruję.")
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)

    current = _last.copy()
    for line in lines:
        if line.startswith("Album Name:"):
            current["album"] = line.replace("Album Name:", "").strip('" .')
        elif line.startswith("Artist:"):
            current["artist"] = line.replace("Artist:", "").strip('" .')
        elif line.startswith("Title:"):
            current["title"] = line.replace("Title:", "").strip('" .')
        elif "Picture received" in line:
            match = re.search(r"length (\d+) bytes", line)
            if match and int(match.group(1)) > 0:
                current["cover_path"] = TMP_COVER

    updated = current != _last
    empty_attempts = 0

    if not any(current.values()):
        print("[DEBUG] Pusty zestaw metadanych — zachowuję poprzednie.")
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)

    if updated:
        _last.update(current)
        print(f"[DEBUG] Nowe metadane: '{_last['title']}' — {_last['artist']} / {_last['album']} / {_last['cover_path']}")
    return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], updated)