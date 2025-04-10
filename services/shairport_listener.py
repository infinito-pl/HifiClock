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

        if not output:
            # Do not clear metadata if no output received
            print("[DEBUG] No metadata output; returning last known values.")
            return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)

        current = _last.copy()

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Album Name:"):
                current["album"] = line.replace("Album Name:", "").strip('" .')
            elif line.startswith("Artist:"):
                current["artist"] = line.replace("Artist:", "").strip('" .')
            elif line.startswith("Title:"):
                current["title"] = line.replace("Title:", "").strip('" .')
            elif line.startswith("Picture received"):
                match = re.search(r"length (\d+) bytes", line)
                if match and int(match.group(1)) > 0:
                    current["cover_path"] = TMP_COVER

        updated = current != _last
        if updated:
            _last.update(current)
            print(f"[DEBUG] Nowe metadane: '{_last['title']}' — {_last['artist']} / {_last['album']} / {_last['cover_path']}")
        else:
            # Reprint current known values for debug clarity
            print(f"[DEBUG] Metadata still current: '{_last['title']}' — {_last['artist']} / {_last['album']} / {_last['cover_path']}")

        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], updated)

    except Exception as e:
        print(f"[DEBUG] Error reading metadata: {e}")
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"], False)