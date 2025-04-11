import os
import sys
import pygame
import threading
import time
from threading import Lock
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import get_current_track_info_shairport
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class MetadataManager:
    def __init__(self):
        self.metadata = {
            "title": None,
            "artist": None,
            "album": None,
            "cover_path": None,
            "active_state": False
        }
        self.lock = Lock()
        self.running = True

    def start(self):
        threading.Thread(target=self._fetch_metadata_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def get_metadata(self):
        with self.lock:
            return self.metadata.copy()

    def _fetch_metadata_loop(self):
        while self.running:
            title, artist, album, cover_path = get_current_track_info_shairport()
            with self.lock:
                prev_active = self.metadata["active_state"]
                self.metadata.update({
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "cover_path": cover_path,
                    "active_state": bool(title and artist and album)
                })
                try:
                    proc = subprocess.Popen(
                        ["/usr/local/bin/shairport-sync-metadata-reader"],
                        stdin=open("/tmp/shairport-sync-metadata", "rb"),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True,
                        bufsize=1
                    )
                    start_time = time.time()
                    while time.time() - start_time < 1.0:
                        line = proc.stdout.readline().strip()
                        if "Resume" in line or "Enter Active State" in line:
                            self.metadata["active_state"] = True
                            break
                        elif "Pause" in line or "Stop" in line or "Exit Active State" in line:
                            self.metadata["active_state"] = False
                            break
                    proc.terminate()
                except Exception as e:
                    logger.error(f"Error checking Shairport state: {e}")

                if prev_active != self.metadata["active_state"]:
                    logger.debug(f"Active state changed to: {self.metadata['active_state']}")
            time.sleep(1)

def main():
    pygame.init()
    pygame.mixer.quit()

    test_mode = "--test" in sys.argv
    screen = pygame.display.set_mode((800, 800), pygame.FULLSCREEN if not test_mode else 0)

    logger.debug("Current SDL driver: %s", pygame.display.get_driver())

    metadata_manager = MetadataManager()
    metadata_manager.start()

    current_screen = "clock"
    manual_switch = None  # Śledzenie ręcznego przełączenia

    while True:
        metadata = metadata_manager.get_metadata()
        is_playing = metadata["active_state"]

        # Automatyczne przełączanie tylko, jeśli nie ma ręcznego przełączenia
        if manual_switch is None:
            if is_playing and current_screen != "player":
                logger.debug("Switching to player screen (auto)...")
                current_screen = "player"
            elif not is_playing and current_screen != "clock":
                logger.debug("Switching to clock screen (auto)...")
                current_screen = "clock"

        if current_screen == "clock":
            result = run_clock_screen(screen, test_mode=test_mode)
            if result == "player":
                logger.debug("Manual switch to player screen")
                current_screen = "player"
                manual_switch = "player"
            elif result is None:
                break
        elif current_screen == "player":
            result = run_player_screen(screen, metadata, test_mode=test_mode)
            if result == "clock":
                logger.debug("Manual switch to clock screen")
                current_screen = "clock"
                manual_switch = "clock"
            elif result is None:
                break

        # Reset manual_switch po krótkim czasie, by pozwolić na automatyczne przełączanie
        if manual_switch is not None:
            time.sleep(0.1)  # Krótka przerwa na ręczne przełączenie
            manual_switch = None

    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.delay(200)
    metadata_manager.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()