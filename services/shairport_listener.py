import os
import subprocess
import time
import logging
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
        # Sprawdź, czy pipe istnieje
        if not os.path.exists(PIPE_PATH):
            logger.error(f"Pipe {PIPE_PATH} does not exist")
            return None, None, None, DEFAULT_COVER

        logger.debug(f"Opening pipe {PIPE_PATH}")
        proc = subprocess.Popen(
            ["/usr/local/bin/shairport-sync-metadata-reader"],
            stdin=open(PIPE_PATH, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Przechwytuj stderr dla debugowania
            text=True,
            bufsize=1
        )

        start_time = time.time()
        timeout = 5.0  # Zwiększony timeout
        while time.time() - start_time < timeout:
            line = proc.stdout.readline().strip()
            if not line:
                continue
            logger.debug(f"Raw line: {line}")

            # Obsługa różnych formatów metadanych
            if line.startswith("Title:"):
                title = line.split("Title: ", 1)[1].strip('".')
                logger.debug(f"Parsed Title: {title}")
            elif line.startswith("Artist:"):
                artist = line.split("Artist: ", 1)[1].strip('".')
                logger.debug(f"Parsed Artist: {artist}")
            elif line.startswith("Album Name:"):
                album = line.split("Album Name: ", 1)[1].strip('".')
                logger.debug(f"Parsed Album: {album}")
            elif "Picture received" in line:
                cover_path = get_latest_cover()
                logger.debug(f"Parsed Cover: {cover_path}")
            elif "Metadata bundle" in line:
                logger.debug("Metadata bundle detected, continuing to parse...")

            # Jeśli mamy wszystkie dane, przerwij
            if title and artist and album:
                break

        # Przechwyć błędy, jeśli występują
        stderr_output = proc.stderr.read()
        if stderr_output:
            logger.error(f"Metadata reader stderr: {stderr_output}")

        proc.terminate()

        # Fallback na MusicBrainz
        if not cover_path or not os.path.isfile(cover_path):
            if title and artist and album:
                cover_path = fetch_and_cache_cover(artist, album)
            else:
                cover_path = DEFAULT_COVER

    except Exception as e:
        logger.error(f"Failed to retrieve metadata: {e}", exc_info=True)
        cover_path = DEFAULT_COVER

    logger.debug(f"Final metadata: Title={title}, Artist={artist}, Album={album}, Cover={cover_path}")
    return title, artist, album, cover_path

if __name__ == "__main__":
    while True:
        title, artist, album, cover = get_current_track_info_shairport()
        print(f"Title: {title}, Artist: {artist}, Album: {album}, Cover: {cover}")
        time.sleep(1)