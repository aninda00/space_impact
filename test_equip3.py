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
# Test equip skin
print(f"'ember' in owned_skins: {'ember' in game.owned_skins}")
game._equip_skin('ember')
print(f'After _equip_skin(ember): player.skin_id={game.player.skin_id}, game.equipped_skin={game.equipped_skin}')
print(f'owned_skins: {game.owned_skins}')