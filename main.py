import pygame
import sys
from core.game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((1080, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Space Impact — Remastered")
    Game(screen).run()


if __name__ == "__main__":
    main()
