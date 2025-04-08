# main.py
import os
import sys

# Wczytujemy argumenty
args = sys.argv
test_mode = "--test" in args
player_mode = "--player" in args

# Jeśli NIE --test, wymuś driver kmsdrm i event1
if not test_mode:
    os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
    os.environ["SDL_EVDEV_TOUCHDEVICE"] = "/dev/input/event1"

import pygame

# Teraz możemy zainicjować pygame
pygame.init()

driver = pygame.display.get_driver()
print("Current SDL driver:", driver)

from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen

def main():
    os.environ["SDL_VIDEO_CENTERED"] = "1"

    screen_to_run = "player" if player_mode else "clock"

    while True:
        if screen_to_run == "clock":
            next_screen = run_clock_screen(test_mode=test_mode)
            # run_clock_screen może zwrócić "player" albo None
            if next_screen == "player":
                screen_to_run = "player"
            else:
                break  # None => user wants to quit
        elif screen_to_run == "player":
            # docelowo run_player_screen może też zwracać "clock"
            next_screen = run_player_screen(test_mode=test_mode)
            if next_screen == "clock":
                screen_to_run = "clock"
            else:
                break

    pygame.quit()

if __name__ == "__main__":
    main()