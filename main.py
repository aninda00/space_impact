import pygame
import sys
from core.game import Game
import ctypes

# Force Windows to register custom taskbar icon
if sys.platform == 'win32':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('spaceimpact.remastered.v1')

def main():
    pygame.init()
    screen = pygame.display.set_mode((1080, 720), pygame.RESIZABLE)
    try:
        game_icon = pygame.image.load("assets/icon.png")
        pygame.display.set_icon(game_icon)
    except Exception as e:
         print(f"Icon load failed: {e}")
    pygame.display.set_caption("Space Impact — Remastered")
    Game(screen).run()


if __name__ == "__main__":
    main()
