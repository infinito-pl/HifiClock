# metadata_shairport.py

import os
import base64
import xml.etree.ElementTree as ET
import select

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"  # lub .png – w trakcie parsowania sprawdzisz magic number

_last = {"title": None, "artist": None, "album": None, "cover_path": None}

def get_current_track_info_shairport():
    DEBUG = True
    if not os.path.exists(PIPE_PATH):
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    try:
        fd = os.open(PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
        rlist, _, _ = select.select([fd], [], [], 0)
        if fd not in rlist:
            os.close(fd)
            return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])
        with os.fdopen(fd, "r") as pipe:
            raw = pipe.read()
    except Exception:
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    try:
        root = ET.fromstring(f"<root>{raw}</root>")
    except ET.ParseError:
        return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])

    for item in root.findall("item"):
        code_elem = item.find("code")
        data_elem = item.find("data")
        if code_elem is None or data_elem is None:
            continue

        try:
            code = bytes.fromhex(code_elem.text).decode("ascii")
        except Exception:
            continue

        try:
            payload = base64.b64decode(data_elem.text.strip())
        except Exception:
            continue

        text = payload.decode("utf-8", errors="replace")
        if code == "minm":
            _last["title"] = text
        elif code == "asar":
            _last["artist"] = text
        elif code == "asal":
            _last["album"] = text
        elif code in ("PICT", "pic ", "covr"):
            try:
                with open(TMP_COVER, "wb") as f:
                    f.write(payload)
                _last["cover_path"] = TMP_COVER
            except:
                pass

        if DEBUG and code in ("minm", "asar", "asal"):
            print(f"[DEBUG] {code}: {text}")
        if DEBUG and code in ("PICT", "pic ", "covr") and _last["cover_path"]:
            print(f"[DEBUG] cover saved to: {_last['cover_path']}")

    return (_last["title"], _last["artist"], _last["album"], _last["cover_path"])
