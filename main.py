# main.py
import os
import sys
import pygame
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen

if __name__ == "__main__":
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()

    args = sys.argv
    test_mode = "--test" in args
    player_mode = "--player" in args

    # Ekran domyślnie: clock
    screen_to_run = "clock"
    if player_mode:
        screen_to_run = "player"

    while True:
        if screen_to_run == "clock":
            next_screen = run_clock_screen(test_mode=test_mode)
            # run_clock_screen może zwrócić "player" albo None
            if next_screen == "player":
                screen_to_run = "player"
            else:
                break  # None => user wants to quit
        elif screen_to_run == "player":
            run_player_screen(test_mode=test_mode)
            # Na razie player wraca zawsze do zegara (lub kończy)
            # Można podobnie w player.py zrobić return "clock" jeśli chcesz
            screen_to_run = "clock"
            # lub break => by zakończyć całkowicie

    pygame.quit()