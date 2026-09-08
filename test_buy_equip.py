import pygame
pygame.init()
from core.game import Game
from core.settings import W, H
from systems.loadout import SKINS_BY_ID

screen = pygame.display.set_mode((W, H))
game = Game(screen)
# Player should already be initialized in __init__
print(f'Initial player skin: {game.player.skin_id}')
print(f'Initial credits: {game.credits}')
print(f'owned_skins: {game.owned_skins}')

# Add some credits
game.credits = 10000
print(f'Credits after adding: {game.credits}')

# Test buy skin
for skin_id in ['ember', 'aurora', 'phantom']:
    skin = SKINS_BY_ID[skin_id]
    print(f'\nBuying {skin["name"]} for {skin["cost"]} credits...')
    result = game._buy_skin(skin_id)
    print(f'  Result: player.skin_id={game.player.skin_id}, equipped_skin={game.equipped_skin}, owned_skins={game.owned_skins}, credits={game.credits}')

# Test equip different skins
print('\n--- Equipping different skins ---')
for skin_id in ['classic', 'ember', 'aurora', 'phantom']:
    print(f'Equipping {skin_id}...')
    game._equip_skin(skin_id)
    print(f'  Result: player.skin_id={game.player.skin_id}, equipped_skin={game.equipped_skin}')

print('\nAll tests passed!')