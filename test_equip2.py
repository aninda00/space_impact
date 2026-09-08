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
print(f'After _equip_skin(ember): player.skin_id={game.player.skin_id}, game.equipped_skin={game.equipped_skin}')
# Direct call
game.player.set_skin('ember')
print(f'After player.set_skin(ember): player.skin_id={game.player.skin_id}')
game.player.set_skin('aurora')
print(f'After player.set_skin(aurora): player.skin_id={game.player.skin_id}')
game.player.set_skin('phantom')
print(f'After player.set_skin(phantom): player.skin_id={game.player.skin_id}')
print('Done')