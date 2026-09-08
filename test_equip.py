import pygame
pygame.init()
from core.game import Game
from core.settings import W, H

screen = pygame.display.set_mode((W, H))
game = Game(screen)
# Player should already be initialized in __init__
print(f'Has player attr: {hasattr(game, "player")}')
print(f'Player: {game.player}')
print(f'Initial player skin: {game.player.skin_id}')
# Test equip skin
game._equip_skin('ember')
print(f'After _equip_skin(ember): {game.player.skin_id}')
game._equip_skin('aurora')
print(f'After _equip_skin(aurora): {game.player.skin_id}')
game._equip_skin('phantom')
print(f'After _equip_skin(phantom): {game.player.skin_id}')
game._equip_skin('classic')
print(f'After _equip_skin(classic): {game.player.skin_id}')
print('All equip tests passed!')