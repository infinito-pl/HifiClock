import os
import sys
import pygame
import threading
import time
from threading import Lock
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen
from services.shairport_listener import get_current_track_info_shairport

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
        """Start the background thread to fetch metadata."""
        threading.Thread(target=self._fetch_metadata_loop, daemon=True).start()

    def stop(self):
        """Stop the metadata fetching thread."""
        self.running = False

    def get_metadata(self):
        """Get a snapshot of the current metadata."""
        with self.lock:
            return self.metadata.copy()

    def _fetch_metadata_loop(self):
        """Continuously fetch metadata in a background thread."""
        while self.running:
            title, artist, album, cover_path = get_current_track_info_shairport()
            with self.lock:
                prev_active = self.metadata["active_state"]
                self.metadata.update({
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "cover_path": cover_path,
                    "active_state": bool(title and artist and album)  # Active if metadata is present
                })
                # Log state changes
                if prev_active != self.metadata["active_state"]:
                    print(f"[DEBUG] Active state changed to: {self.metadata['active_state']}")
            time.sleep(1)  # Adjust polling frequency as needed

def main():
    pygame.init()
    pygame.mixer.quit()

    test_mode = "--test" in sys.argv
    screen = pygame.display.set_mode((800, 800), pygame.FULLSCREEN if not test_mode else 0)

    print("Current SDL driver:", pygame.display.get_driver())

    # Initialize metadata manager
    metadata_manager = MetadataManager()
    metadata_manager.start()

    current_screen = "clock"

    while True:
        metadata = metadata_manager.get_metadata()
        is_playing = metadata["active_state"]

        # Switch to player screen when playback starts
        if is_playing and current_screen != "player":
            print("[DEBUG] Switching to player screen...")
            current_screen = "player"
        # Switch to clock screen when playback stops
        elif not is_playing and current_screen != "clock":
            print("[DEBUG] Switching to clock screen...")
            current_screen = "clock"

        if current_screen == "clock":
            result = run_clock_screen(screen, test_mode=test_mode)
            if result == "player":
                current_screen = "player"
            elif result is None:
                break
        elif current_screen == "player":
            result = run_player_screen(screen, metadata, test_mode=test_mode)
            if result == "clock":
                current_screen = "clock"
            elif result is None:
                break

    # Clean up
    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.delay(200)
    metadata_manager.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()