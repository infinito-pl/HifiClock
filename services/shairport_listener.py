import os
import subprocess
import time
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,  # Poziom logowania
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Global variables for metadata tracking
last_title = last_artist = last_album = last_cover = None
active_state = False
should_switch_to_player = False
should_switch_to_clock = False

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"  # or .png, magic number check is done during parsing

# Function to read and fetch metadata from shairport-sync-metadata-reader
def get_current_track_info_shairport():
    global last_title, last_artist, last_album, last_cover

    title = artist = album = cover_path = None
    logger.debug("Starting to fetch track info from shairport-sync-metadata-reader.")
    start_time = time.time()

    while time.time() - start_time < 5.0:  # Dłuższy czas na próbę pobrania metadanych
        try:
            proc = subprocess.Popen(
                ["/usr/local/bin/shairport-sync-metadata-reader"],
                stdin=open(PIPE_PATH, "rb"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )

            for line in proc.stdout:
                line = line.strip()
                logger.debug(f"Received line: {line}")

                if line.startswith("Title:"):
                    title = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Extracted Title: {title}")
                elif line.startswith("Artist:"):
                    artist = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Extracted Artist: {artist}")
                elif line.startswith("Album Name:"):
                    album = line.split(': "', 1)[1].strip('".')
                    logger.debug(f"Extracted Album: {album}")
                elif "Picture received" in line and "length" in line:
                    cover_path = "/tmp/shairport-sync/.cache/coverart/last_cover.png"
                    logger.debug(f"Cover path set to: {cover_path}")
                if title and artist and album:  # Jeśli wszystkie metadane są dostępne, zakończ pętlę
                    break
            proc.terminate()

            if title and artist and album:
                break  # Metadane pobrane, zakończ próbę

        except Exception as e:
            logger.error(f"Failed to retrieve metadata: {e}")
            return None, None, None, None

    if cover_path and os.path.isfile(cover_path):
        last_cover = cover_path
        logger.debug(f"Found cover: {cover_path}")
    else:
        last_cover = None
        logger.debug("No cover found.")

    last_title = title
    last_artist = artist
    last_album = album

    logger.debug(f"Metadata: Title={title}, Artist={artist}, Album={album}, Cover={cover_path}")
    return title, artist, album, cover_path

# Function to listen to shairport state and control UI changes
def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover, active_state, should_switch_to_player, should_switch_to_clock

    start_time = time.time()  # Timeout handling

    while time.time() - start_time < 5.0:
        try:
            proc = subprocess.Popen(
                ["/usr/local/bin/shairport-sync-metadata-reader"],
                stdin=open(PIPE_PATH, "rb"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )

            for line in proc.stdout:
                line = line.strip()

                if "Enter Active State" in line:
                    active_state = True
                    should_switch_to_player = True
                    should_switch_to_clock = False
                    logger.debug("Shairport entered active state")

                elif "Exit Active State" in line:
                    active_state = False
                    should_switch_to_player = False
                    should_switch_to_clock = True
                    logger.debug("Shairport exited active state")

                # Regularly fetch metadata when active
                if active_state:
                    title, artist, album, cover_path = get_current_track_info_shairport()
                    if title != last_title or artist != last_artist or album != last_album:
                        last_title, last_artist, last_album, last_cover = title, artist, album, cover_path
                        logger.debug("Metadata updated")

                # Timeout after a set period
                if time.time() - start_time > 5.0:
                    logger.debug("Timeout reached, breaking loop")
                    break

            proc.terminate()

        except Exception as e:
            logger.error(f"Error in reading shairport metadata: {e}")
        time.sleep(3)  # Wait for 3 seconds before the next attempt

# Main function to start the listener
if __name__ == "__main__":
    while True:
        read_shairport_metadata()
        time.sleep(1)