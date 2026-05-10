import pygame
from core.game import Game
pygame.init()
screen = pygame.display.set_mode((1080,720))
g = Game(screen)
print('initial state', g.state)
# Simulate click on CAMPAIGN in main menu
btn = g.menu._btn_campaign
print('campaign rect', btn.rect)
ww, wh = pygame.display.get_surface().get_size()
pos = (int(btn.rect.centerx * ww / 1920), int(btn.rect.centery * wh / 1080))
print('campaign window click', pos)
e = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
orig_get = pygame.event.get
pygame.event.get = lambda: [e]
g._handle_events()
print('state after campaign click', g.state, g.menu._screen)
# Now simulate click on NEW CAMPAIGN in campaign screen
btn = g.menu._btn_play
pos = (int(btn.rect.centerx * ww / 1920), int(btn.rect.centery * wh / 1080))
print('play window click', pos)
e2 = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
pygame.event.get = lambda: [e2]
g._handle_events()
print('state after play click', g.state)
pygame.event.get = orig_get
pygame.quit()
