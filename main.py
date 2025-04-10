# main.py
import os
import sys
import pygame
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen

def get_current_track_info_shairport():
    # Mock function to emulate getting track info from Shairport
    # Replace this with actual implementation
    return None, None, None, None

def main():
    pygame.init()
    pygame.mixer.quit()

    test_mode = "--test" in sys.argv
    if test_mode:
        screen = pygame.display.set_mode((800, 800))
    else:
        screen = pygame.display.set_mode((800, 800), pygame.FULLSCREEN)

    print("Current SDL driver:", pygame.display.get_driver())

    current_screen = "clock"
    last_playing_status = None  # Zmienna do monitorowania stanu odtwarzania

    while True:
        title, artist, album, cover_path = get_current_track_info_shairport()

        if current_screen == "clock":
            result = run_clock_screen(screen, test_mode=test_mode)
            if result == "player":
                current_screen = "player"
            else:
                break
        elif current_screen == "player":
            result = run_player_screen(screen, test_mode=test_mode)
            if result == "clock":
                current_screen = "clock"
            elif title is None or artist is None:  # Sprawdzenie, czy muzyka jest zatrzymana
                current_screen = "clock"  # Jeśli brak danych z Shairport, wracamy na zegar
            else:
                # Muzyka wciąż odtwarzana
                last_playing_status = (title, artist, album, cover_path)
                continue

    # Wyczyść ekran przed wyjściem
    screen.fill((0, 0, 0))
    pygame.display.flip()
    time.sleep(0.2)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()