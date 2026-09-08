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
print(f'owned_skins: {game.owned_skins}')
print(f'equipped_skin: {game.equipped_skin}')

# First buy the skin
game.owned_skins.add('ember')
print(f"After adding ember to owned_skins: {game.owned_skins}")
# Test equip skin
game._equip_skin('ember')
print(f'After _equip_skin(ember): player.skin_id={game.player.skin_id}, game.equipped_skin={game.equipped_skin}')

# Test other skins
game.owned_skins.add('aurora')
game.owned_skins.add('phantom')
game._equip_skin('aurora')
print(f'After _equip_skin(aurora): player.skin_id={game.player.skin_id}')
game._equip_skin('phantom')
print(f'After _equip_skin(phantom): player.skin_id={game.player.skin_id}')
game._equip_skin('classic')
print(f'After _equip_skin(classic): player.skin_id={game.player.skin_id}')
print('Done')