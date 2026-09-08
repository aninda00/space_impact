import pygame
pygame.init()
from entities.player import Player
from core.settings import W, H
from systems.loadout import SKINS_BY_ID

screen = pygame.display.set_mode((W, H))

# Test all skins
for skin_id, skin in SKINS_BY_ID.items():
    player = Player(skin_id=skin_id)
    print(f'Skin {skin_id}: body={skin["colors"]["body"]}, nose={skin["colors"]["nose"]} - OK')

# Test dynamic skin change
player = Player(skin_id='classic')
print(f'Initial skin: {player.skin_id}')
player.set_skin('ember')
print(f'After set_skin(ember): {player.skin_id}')
player.set_skin('aurora')
print(f'After set_skin(aurora): {player.skin_id}')
player.set_skin('phantom')
print(f'After set_skin(phantom): {player.skin_id}')
print('All skin tests passed!')