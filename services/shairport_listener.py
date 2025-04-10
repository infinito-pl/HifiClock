import os
import subprocess
import time

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
        for line in proc.stdout:
            line = line.strip()

            if line.startswith("Title:"):
                title = line.split(': "', 1)[1].strip('".')
            elif line.startswith("Artist:"):
                artist = line.split(': "', 1)[1].strip('".')
            elif line.startswith("Album Name:"):
                album = line.split(': "', 1)[1].strip('".')
            elif "Picture received" in line and "length" in line:
                cover_path = "/tmp/shairport-sync/.cache/coverart/last_cover.png"

            if time.time() - start_time > 1.0:  # Timeout for metadata retrieval
                break

        proc.terminate()

    except Exception as e:
        return None, None, None, None

    # Checking if cover exists
    if cover_path and os.path.isfile(cover_path):
        last_cover = cover_path
    else:
        last_cover = None

    last_title = title
    last_artist = artist
    last_album = album

    return title, artist, album, cover_path

# Function to listen to shairport state and control UI changes
def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover, active_state, should_switch_to_player, should_switch_to_clock

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

            elif "Exit Active State" in line:
                active_state = False
                should_switch_to_player = False
                should_switch_to_clock = True

            # Continuously fetch metadata when active
            if active_state:
                title, artist, album, cover_path = get_current_track_info_shairport()
                if title != last_title or artist != last_artist or album != last_album:
                    last_title, last_artist, last_album, last_cover = title, artist, album, cover_path

            # Timeout to break the loop after a certain duration
            if time.time() - start_time > 5.0:
                break

        proc.terminate()

    except Exception as e:
        print(f"Error in metadata listener: {e}")

# Main function to start the listener
if __name__ == "__main__":
    while True:
        read_shairport_metadata()
        time.sleep(1)