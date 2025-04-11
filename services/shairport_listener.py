import os
import subprocess
import time
import logging
import json
import glob
from services.musicbrainz_cover import fetch_and_cache_cover

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

PIPE_PATH = "/tmp/shairport-sync-metadata"
COVER_CACHE_DIR = "/tmp/shairport-sync/.cache/coverart"
DEFAULT_COVER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images", "cover.png")

def get_latest_cover():
    try:
        covers = glob.glob(os.path.join(COVER_CACHE_DIR, "cover-*.jpg"))
        if covers:
            return max(covers, key=os.path.getctime)
    except Exception as e:
        logger.error(f"Error finding latest cover: {e}")
    return None

def get_current_track_info_shairport():
    title = artist = album = cover_path = None
    try:
        proc = subprocess.Popen(
            ["/usr/local/bin/shairport-sync-metadata-reader"],
            stdin=open(PIPE_PATH, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        start_time = time.time()
        while time.time() - start_time < 2.0:  # Reduced timeout for responsiveness
            line = proc.stdout.readline().strip()
            if not line:
                continue
            logger.debug(f"Received line: {line}")

            if line.startswith("Title:"):
                title = line.split(': "', 1)[1].strip('".')
            elif line.startswith("Artist:"):
                artist = line.split(': "', 1)[1].strip('".')
            elif line.startswith("Album Name:"):
                album = line.split(': "', 1)[1].strip('".')
            elif "Picture received" in line and "length" in line:
                cover_path = get_latest_cover()

            if title and artist and album:
                break

        proc.terminate()

        # Fallback to MusicBrainz if no cover from Shairport
        if not cover_path or not os.path.isfile(cover_path):
            if title and artist and album:
                cover_path = fetch_and_cache_cover(artist, album)
            else:
                cover_path = DEFAULT_COVER

    except Exception as e:
        logger.error(f"Failed to retrieve metadata: {e}")
        cover_path = DEFAULT_COVER

    logger.debug(f"Metadata: Title={title}, Artist={artist}, Album={album}, Cover={cover_path}")
    return title, artist, album, cover_path

if __name__ == "__main__":
    while True:
        title, artist, album, cover = get_current_track_info_shairport()
        print(f"Title: {title}, Artist: {artist}, Album: {album}, Cover: {cover}")
        time.sleep(1)