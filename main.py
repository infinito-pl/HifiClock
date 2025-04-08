# main.py
import os
import sys
import pygame
from assets.screens.clock import run_clock_screen
from assets.screens.player import run_player_screen

def main():
    # Ewentualne ustawienia drivera / event1 / test_mode itp.
    # Dla uproszczenia zakładamy, że to już zrobione przed importami
    # lub na podstawie sys.argv

    pygame.init()
    pygame.mixer.quit()

    # Ustal, czy test_mode (okno) czy fullscreen
    test_mode = "--test" in sys.argv
    if test_mode:
        screen = pygame.display.set_mode((800, 800))
    else:
        screen = pygame.display.set_mode((800, 800), pygame.FULLSCREEN)

    print("Current SDL driver:", pygame.display.get_driver())

    # Na start – np. ekran clock
    current_screen = "clock"

    while True:
        if current_screen == "clock":
            result = run_clock_screen(screen, test_mode=test_mode)
            if result == "player":
                current_screen = "player"
            else:
                # result == None lub "quit"
                break
        elif current_screen == "player":
            result = run_player_screen(screen, test_mode=test_mode)
            if result == "clock":
                current_screen = "clock"
            else:
                break

    pygame.quit()

if __name__ == "__main__":
    main()