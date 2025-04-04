import os
import sys
import pygame
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen

if __name__ == "__main__":
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()

    # Read arguments
    args = sys.argv
    test_mode = "--test" in args
    player_mode = "--player" in args

    # Decide which screen to launch
    if player_mode:
        run_player_screen(test_mode=test_mode)
    else:
        run_clock_screen(test_mode=test_mode)

    pygame.quit()
