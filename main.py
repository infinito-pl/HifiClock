import os
import pygame
import sys
from assets.screens.clock import run_clock_screen

if __name__ == "__main__":
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    test_mode = "--test" in sys.argv
    run_clock_screen(test_mode=test_mode)
    pygame.quit()