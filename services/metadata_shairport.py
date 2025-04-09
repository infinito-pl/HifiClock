# metadata_shairport.py

import os
import select
import struct
import time

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"  # lub .png – w trakcie parsowania sprawdzisz magic number

_last = {"title": None, "artist": None, "album": None, "cover_path": None}

def get_current_track_info_shairport():
    """
    Nieblokujące odczytywanie metadanych z potoku Shairport Sync w formacie chunków.
    Zwraca (title, artist, album, cover_path).
    Jeżeli brak danych w potoku – zwraca poprzednie metadane lub (None, None, None, None).
    """

    if not os.path.exists(PIPE_PATH):
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    try:
        fd = os.open(PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    rlist, _, _ = select.select([fd], [], [], 0)
    if fd not in rlist:
        os.close(fd)
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    try:
        raw_data = os.read(fd, 65536)
    except OSError:
        os.close(fd)
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    os.close(fd)
    if not raw_data:
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    idx = 0
    data_len = len(raw_data)

    title = None
    artist = None
    album = None
    cover_path = None

    while idx < data_len:
        if (idx + 16) > data_len:
            break

        signature = raw_data[idx:idx+4]
        if signature != b'ssnc':
            idx += 1
            continue

        code = raw_data[idx+4:idx+8]
        length_bytes = raw_data[idx+8:idx+16]
        length = struct.unpack(">Q", length_bytes)[0]

        idx += 16
        if idx + length > data_len:
            break

        payload = raw_data[idx: idx + length]
        idx += length

        if code == b'minm':
            title = payload.decode("utf-8", errors="replace")
        elif code == b'asar':
            artist = payload.decode("utf-8", errors="replace")
        elif code == b'asal':
            album = payload.decode("utf-8", errors="replace")
        elif code in (b'PICT', b'pic ', b'covr'):
            try:
                with open(TMP_COVER, "wb") as f:
                    f.write(payload)
                cover_path = TMP_COVER
            except:
                pass

    if title:
        _last["title"] = title
    if artist:
        _last["artist"] = artist
    if album:
        _last["album"] = album
    if cover_path:
        _last["cover_path"] = cover_path

    return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

title, artist, album, cover_path = get_current_track_info_shairport()
print("[DEBUG] track info:", title, artist, album, cover_path)